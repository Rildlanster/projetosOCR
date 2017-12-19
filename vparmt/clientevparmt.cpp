/**
 * -Aplicação roda uma thread em loop infinito lendo um diretório de imagens.
 * -As imagens em formato WEBP são decodificadas.
 * -Cada imagem lida do diretório é renomeada e submetida para processamento do OCR na forma assíncrona.
 * -A imagem é renomeada (adiciona um prefixo) para que a thread não leia novamente a imagem que
 * está em processamento na engine do OCR.
 * -O OCR chama função de callback após o processamento. Nesta função a imagem é excluída e um arquivo
 * de saída TXT com os resultados é gerado.
 * -A licença do OCR VPAR permite o uso simultâneo de 16 núcleos.
 * -A thread de leitura de imagens é capaz de manter os 16 núcleos ocupados, pois o tempo de preparação
 * da imagem para processamento é bem menor que o tempo de processamento de cada imagem no OCR.
 * -O OCR gasta de 100 a 500 ms (ou mais) para processar cada imagem, enquanto a decodificação e escrita
 * de arquivos WEBP gasta entre 5 e 11 ms, em testes realizados. Arquivos em outros formatos que
 * não precisem de decodificação são apenas renomeados e imediatamente submetidos para processamento
 * pelo OCR. Assim, o WEBP representa o tempo do pior caso.
 * -A função de callback precisa ser reentrant, pois várias threads (até 16) do OCR chamam esta função
 * para processar o resultado.
 * O sistema de arquivos usado para as imagens é em memória. Criar com mount -t tmpfs -o size=500M,mode=1777 tmpfs /opt/data/ocrVpar
 *
 * TODO: Melhorar o paralelismo:
 * -Criar thread <th1> que apenas lê imagens de um diretório <dir1>, decodifica (se formato WEBP)
 * e move-as para um diretório <dir2>.
 * -Thread <th2> lê imagens em <dir2> e imediatamente submete ao OCR para processamento.
 * -Verificar se a função de callback ocupa um dos 16 núcleos licenciados até o fim de sua execução.
 * Se ocupar, alterar o callback para apenas escrever em uma estrutura em memória (lock necessário)
 * as informações produzidas pelo OCR. Criar thread <th3> que lê a estrutura em memória e
 * escreve os resultados do OCR em arquivos de saída. Assim, a função de callback chamada pela
 * engine do VPAR não permanece na pilha de execução que contém a função ejecutarReconocimiento
 * da engine.
 * -As opções acima representam, IMHO, um cenário ótimo onde os núcleos licenciados podem estar
 * sempre ocupados processando uma imagem, com mínimo sequenciamento de outras tarefas, como a
 * decoficação de imagens.
 *
 * Author: Rodrigo Nogueira
 * Date: 2017 november
 */
#include "vparmt.h"
#include <iostream>
#include <pthread.h>
#include <time.h>
#include <string.h>
#include <cstring>
#include <stdio.h>
#include <stdlib.h>
#include <dlfcn.h>
#include <dirent.h>
#include <queue>
#include <string>
#include <time.h>
#include <iostream>
#include <unistd.h>
#include <sys/stat.h>

#define IS_TESTING true
#define NANO_SECOND_MULTIPLIER 1000000L  //1 millisecond = 1000000 Nanoseconds
const long INTERVAL_MS = 999 * NANO_SECOND_MULTIPLIER;
#define MAX_FILE_NAME_LENGTH 150
//Prefixo utilizado para marcar arquivos que estão em processamento.
#define FILE_PROCESSING_PREFIX "v__"

#if IS_TESTING
const char IMG_BASE_PATH_IN[] = "/opt/data/ocrVpar/in";
#else
const char IMG_BASE_PATH_IN[] = "/opt/data/ocrVpar/in";
#endif
const char IMG_BASE_PATH_OUT[] = "/opt/data/ocrVpar/out";

//int MAX_QUEUE_SIZE = 0; //valor definido com base na qtde de processadores licenciados na máquina.

#define SPAIN_COUNTRY_CODE 101; //para testes com as imagens que acompanham a instalação do VPAR.
#define BRAZIL_COUNTRY_CODE 203;
const long COUNTRY_CODE = BRAZIL_COUNTRY_CODE;

typedef long (*fvparmtInit)(callbackRes call, long lCountryCode, long lAvCharacterHeight, bool bDuplicateLines, bool bSort2LinesPLates,bool bTrucks,bool Trace);
typedef void (*fvparmtEnd)();
typedef long (*fvparmtQueueSize)();
typedef long (*fvparmtFreeCores)();
typedef long (*fvparmtLicensedCores)();

typedef long (*fvparmtRead)(tRecognitionEngineSettings *Conf, long lWidth, long lHeight, unsigned char* pbImageData);
typedef long (*fvparmtReadRGB24)(tRecognitionEngineSettings *Conf, long lWidth, long lHeight, unsigned char* pbImageDataRGB,bool bFlip );
typedef long (*fvparmtReadRGB32)(tRecognitionEngineSettings *Conf, long lWidth, long lHeight, unsigned char* pbImageDataRGB,bool bFlip );
typedef long (*fvparmtReadBMP)(tRecognitionEngineSettings *Conf, char* pcFilename);
typedef long (*fvparmtReadJPG)(tRecognitionEngineSettings *Conf, char* pcFilename);

//Estrutura para o arquivo de entrada
typedef struct {
	char fileId[MAX_FILE_NAME_LENGTH];
	char imgFile[MAX_FILE_NAME_LENGTH];
} OcrInInfo;

void* hVPARMTlib;
fvparmtInit pVPARMTInit;
fvparmtEnd pVPARMTEnd;
fvparmtQueueSize pVPARMTQueueSize;
fvparmtFreeCores pVPARMTFreeCores;
fvparmtLicensedCores pVPARMTLicensedCores;
fvparmtRead pVPARMTRead;
fvparmtReadRGB24 pVPARMTReadRGB24;
fvparmtReadRGB32 pVPARMTReadRGB32;
fvparmtReadBMP pVPARMTReadBMP;
fvparmtReadJPG pVPARMTReadJPG;

long callbackReadyResult(long id, tResults* result);
void SetVPARConf(tRecognitionEngineSettings &conf);
OcrInInfo* getNextImgFile();

/**
 * Função a ser executada por uma única thread, que lê um diretório com arquivos de imagens
 * e submete para processamento OCR. Para utilizar múltiplas threads será necessário incluir
 * locks e/ou alterar funções não reentrant.
 */
void *threadOCRProcessor(void* param) {
    tRecognitionEngineSettings conf;
	SetVPARConf(conf);
#if IS_TESTING
	const int licensedCores = pVPARMTLicensedCores();
	long freeCoresOccurrence[licensedCores+1];
	memset(freeCoresOccurrence, 0, (licensedCores+1)*sizeof(long));
#endif

	while(true)	{
//		long qsize = pVPARMTQueueSize();
		long freeCores = pVPARMTFreeCores();
#if IS_TESTING
		if(freeCores < licensedCores) {
			freeCoresOccurrence[freeCores]++;
			printf("* Free/licensed cores: %d / %d *\n", freeCores, licensedCores);
			for(int i = 0; i <= licensedCores; i++)
				printf("%02d free %d times, ", i, freeCoresOccurrence[i]);
			printf("\n");
		}
#endif
		if (freeCores > 0)	{
			OcrInInfo* ocrInInfo = getNextImgFile();
			if(ocrInInfo == NULL) {
				nanosleep((const struct timespec[]){{0, INTERVAL_MS}}, NULL);
				continue;
			}
			conf.lUserParam1 = ocrInInfo; //a memória da estrutura deve ser liberada posteriormente
			pVPARMTReadBMP(&conf, ocrInInfo->imgFile);
		}
		else {
			printf("*** Sem núcleos disponíveis ***\n");
#if IS_TESTING
			sleep(3);
#endif
		}
	}

    return 0;
}

/*
 * Verifica se é um arquivo regular.
 */
bool isRegularFile(const char* dir, const char* file) {
	struct stat st;
	char filename[MAX_FILE_NAME_LENGTH];
	snprintf(filename, sizeof(filename), "%s/%s", dir, file);
	stat(filename, &st);
	return S_ISREG(st.st_mode);
}

/*
 * Verifica se o arquivo tem extensao webp e converte a imagem.
 * O arquivo webp é REMOVIDO.
 */
void preprocessFile(OcrInInfo* processingFileInfo, const char* dir, const char* fName) {
	//busca a extensão do arquivo
	const char *fileExt = (strrchr(fName, '.') != NULL)? strrchr(fName, '.') + 1 : "\0";
	char fullFName[MAX_FILE_NAME_LENGTH];
	if(strlen(fileExt) < 3) //obrigatório ter uma extensão
		return;
	//preenche a estrutura processingFileInfo e renomea o arquivo.
	sprintf(fullFName, "%s/%s", dir, fName);
	int idFileSize = strlen(fName) - strlen(fileExt) - 1;
	strncpy(processingFileInfo->fileId, fName, idFileSize);
	processingFileInfo->fileId[idFileSize] = '\0';
	printf("processingFileInfo->fileId = %s\nfName = %s\nfileExt = %s\n", processingFileInfo->fileId, fName, fileExt);
	if(strcasecmp(fileExt, "WEBP")) { //se nao é webp, renomea o arquivo e retorna
		sprintf(processingFileInfo->imgFile, "%s/%s%s", dir, FILE_PROCESSING_PREFIX, fName);
		rename(fullFName, processingFileInfo->imgFile);
		return;
	}

	//Decodifica arquivos WEBP. O arquivo de saída será um BMP.
	sprintf(processingFileInfo->imgFile, "%s/%s%.*s.bmp", dir, FILE_PROCESSING_PREFIX, strlen(fName)-5, fName); //nome do arquivo de saida para processamento.
	char command[100 + 2*MAX_FILE_NAME_LENGTH];
	sprintf(command, "dwebp %s -bmp -v -o %s", fullFName, processingFileInfo->imgFile);
	system(command);
	remove(fullFName);
}
//********************************************

/*
 * Procura no diretório padrão por imagens ainda não analisadas.
 *
 * O diretório em análise é mantido aberto pelas estruturas estáticas da função.
 * Desta forma, não se abre o diretório nem se verifica desnecessariamente
 * arquivos/diretórios já verificados em chamadas anteriores a esta função.
 *
 * FUNÇÃO NÃO REENTRANT.
 */
OcrInInfo* getNextImgFile() {
	static DIR *d = NULL;
	static struct dirent *dirInfo = NULL;
	OcrInInfo* ocrInInfo = NULL;

	if(dirInfo == NULL) {
		closedir(d);
		d = opendir(IMG_BASE_PATH_IN);
	}
	//Percorre o diretório até encontrar um arquivo regular para processamento.
	while(((dirInfo = readdir(d)) != NULL) &&
			( !isRegularFile(IMG_BASE_PATH_IN, dirInfo->d_name) ||
			(strncmp(dirInfo->d_name, FILE_PROCESSING_PREFIX, 3) == 0) ) //desconsidera os arquivos renomeados, q já estao em processamento.
		);
	if(dirInfo != NULL) {
		ocrInInfo = (OcrInInfo*)malloc(sizeof(OcrInInfo)); //memória liberada posteriomente na função de callback.
		preprocessFile(ocrInInfo, IMG_BASE_PATH_IN, dirInfo->d_name);
	}

	return ocrInInfo;
}

int initVPAR() {
	hVPARMTlib = dlopen("vparmt.so",RTLD_LAZY);

    pVPARMTInit = (fvparmtInit)dlsym(hVPARMTlib, "vparmtInit");
    pVPARMTEnd = (fvparmtEnd)dlsym(hVPARMTlib, "vparmtEnd");
    pVPARMTRead = (fvparmtRead)dlsym(hVPARMTlib, "vparmtRead");
	pVPARMTReadRGB24 = (fvparmtReadRGB24)dlsym(hVPARMTlib, "vparmtReadRGB24");
	pVPARMTReadRGB32 = (fvparmtReadRGB32)dlsym(hVPARMTlib, "vparmtReadRGB32");
	pVPARMTReadBMP = (fvparmtReadBMP)dlsym(hVPARMTlib, "vparmtReadBMP");
	pVPARMTReadJPG = (fvparmtReadJPG)dlsym(hVPARMTlib, "vparmtReadJPG");
	pVPARMTQueueSize = (fvparmtQueueSize)dlsym(hVPARMTlib, "vparmtQueueSize");
	pVPARMTFreeCores = (fvparmtFreeCores)dlsym(hVPARMTlib, "FreeCores");
	pVPARMTLicensedCores = (fvparmtLicensedCores)dlsym(hVPARMTlib, "NumLicenseCores");

	printf("Init library...\n");
	printf("Country code: %d\n", COUNTRY_CODE);

    return pVPARMTInit(callbackReadyResult, COUNTRY_CODE,-1, false, false, false, false);
}

int main(int argc, char* argv[]) {
	if(!initVPAR()) {
		printf("ERROR: Problem when initializing VPAR.\n");
		return 1;
	}
	printf("Init OK\n");
//	MAX_QUEUE_SIZE = 2 * pVPARMTFreeCores();

	pthread_t handleOCRProcessor;
	pthread_create(&handleOCRProcessor, NULL, threadOCRProcessor, NULL);
	pthread_join(handleOCRProcessor, NULL);
	pVPARMTEnd();

	return 0;
}

/**
 * Funções de limpeza do sistema.
 */
void fileSysCleanup() {
	//limpa os arquivos que iniciem com v__.
	//system("find /opt/data/ocrVpar/in/ -type f -name v__\\* -exec rm {} \\;");
	//limpa arquivos do diretório de in/out q tenham mais de x minutos.
	system("find /opt/data/ocrVpar/in -mmin +3 -type f -delete");
	system("find /opt/data/ocrVpar/out -mmin +3 -type f -delete");
}

/*
 * Função (reentrant) de callback, chamada pela engine VPAR após realizar o OCR.
 */
long callbackReadyResult(long identificador, tResults* resultados) {
	static unsigned long long int counter = 0;
	char *outFileName = (char *)malloc(sizeof(char) * MAX_FILE_NAME_LENGTH);
	OcrInInfo* ocrInInfo = (OcrInInfo*)resultados->lUserParam1;

	sprintf(outFileName, "%s/%s.txt", IMG_BASE_PATH_OUT, ocrInInfo->fileId);
	FILE* fp = fopen(outFileName, "w");
	free(outFileName);
	if(!fp) {
		printf("Output file error for ID: %d and file name: %s\n", identificador, ocrInInfo->fileId);
		return 1;
	}
	if ((resultados->lRes == 1) && (resultados->lNumberOfPlates > 0)) {
#if IS_TESTING
		printf("Placa id %d: %s. tempo: %d ms.\n", identificador, resultados->strResult[0], resultados->lProcessingTime);
#endif
		fprintf(fp, "placa: %s\n", resultados->strResult[0]);
		fprintf(fp, "tempoProcessamento: %d\n", resultados->lProcessingTime);
		fprintf(fp, "confiancaGlobal: %f\n", resultados->vlGlobalConfidence[0]);
		fprintf(fp, "alturaMediaChar: %f\n", resultados->vfAverageCharacterHeight[0]);
		fprintf(fp, "placaRetEsq: %d\n", resultados->vlLeft[0]);
		fprintf(fp, "placaRetTopo: %d\n", resultados->vlTop[0]);
		fprintf(fp, "placaRetDir: %d\n", resultados->vlRight[0]);
		fprintf(fp, "placaRetBase: %d\n", resultados->vlBottom[0]);
		fprintf(fp, "char1: %d,%d,%d,%d\n"
				, resultados->vlCharacterPosition[0][0][0], resultados->vlCharacterPosition[0][0][1]
                , resultados->vlCharacterPosition[0][0][2], resultados->vlCharacterPosition[0][0][3]);
	}
	else
	{
		printf("Nenhum resultado para o id %d\n", identificador);
		fprintf(fp, "placa: 0\n");
	}
	fclose(fp);
	remove(ocrInInfo->imgFile);
	free(ocrInInfo);
	//Periodicamente, roda um cleanup.
	counter++; //essa linha juntamente com a proxima nao sao threadsafe, mas nao há dano consideravel.
	if((counter % 1000) == 0) {
		printf("%llu imagens lidas com OCR.\n", counter);
//		fileSysCleanup();
	}
	return 0;
}

/**
 * Ajusta as configurações do VPAR (ver na documentação do VPAR o significado de cada parâmetro).
 */
void SetVPARConf(tRecognitionEngineSettings &conf) {
	conf.lMiliseconds = 0;
	conf.bAplicarCorreccion = false;
	conf.fDistance = 0;
	conf.fVerticalCoeff = 0;
	conf.fHorizontalCoeff = 0;
	conf.fAngle = 0;
	conf.fRadialCoeff = 0;
	conf.fVerticalSkew = 0;
	conf.fHorizontalSkew =0;
	conf.lNumSteps = 0;
	conf.vlSteps[0] = 20;
	conf.vlSteps[1] = 60;
	conf.vlSteps[2] = 35;
	conf.vlSteps[3] = 40;
	conf.vlSteps[4] = 45;
	conf.vlSteps[5] = 50;
	conf.vlSteps[6] = 55;
	conf.vlSteps[7] = 60;
	conf.lLeft = 0;
	conf.lTop = 0;
	conf.lWidth = 0;
	conf.lHeight = 0;
	conf.fScale = 1;
	conf.CharacterRectangle = false;
	conf.SlantDetection = 1;
	conf.KillerShadow= 0;
}
