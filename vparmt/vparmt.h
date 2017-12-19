/*
 * vparmt.h
 *
 *  Created on: Jun 11, 2012
 *      Author: user
 */

#ifndef VPARMT_H_
#define VPARMT_H_

#define PREFIX(FNAME) vparmt##FNAME

#define MAX_PLATES 8
#define MAX_CHARACTERS 10
#define MAX_STEPS 8
#define INT_MAX       2147483647    /* maximum (signed) int value */
#define MAX_FILE_PATH 200
#define RUTA_PACK "/usr/lib64/map"


/////////////////////////////////////////////////////////////
// CONFIGURATION STRUCTURE FOR THE RECOGNITION ENGINE      //
/////////////////////////////////////////////////////////////

// All the configuration parameters are encapsulated into this structure
// and then passed as arguments to all the 'READ' calls.
/////////////////////////////////////////////////////////////

typedef struct
{
	//Time
	long lMiliseconds;

	//Correction Coefficients
	long bAplicarCorreccion;	// The next 4 fields are applied only if this boolean field is true.
	float fDistance;
	float fVerticalCoeff;
	float fHorizontalCoeff;
	float fAngle;
	float fRadialCoeff;
    float fVerticalSkew;
	float fHorizontalSkew;

	//Automatic Character Height
	long lNumSteps;
						//can be 0 if you donŽt want to set the character height range or 2 if you want to set the min and max height interval in the first 2 possitions of the next array.
	long vlSteps[MAX_STEPS];

	//Rectangle
	long lLeft;
	long lTop;
	long lWidth;
	long lHeight;
	float fScale;		//1 means no scale correction
	void* lUserParam1;
	void* lUserParam2;
	void* lUserParam3;
	long SlantDetection;
	long KillerShadow;
	bool CharacterRectangle; //si true se guarda imagen y se devuelven rectangulos



} tRecognitionEngineSettings;



//////////////////////////////////////////////////////////////////
// STRUCTURE THAT CONTAINS THE RETURNED RESULTS                 //
//////////////////////////////////////////////////////////////////

// All the results are returned in the callback function within this structure.

// All the results are returned in the callback function within this structure.
typedef struct
{

	long lRes;
	long lNumberOfPlates;
	char strResult[MAX_PLATES][MAX_CHARACTERS];
	long vlNumbersOfCharacters[MAX_PLATES];
	float vlGlobalConfidence[MAX_PLATES];
	float vfAverageCharacterHeight[MAX_PLATES];
	float vfCharacterConfidence[MAX_PLATES][MAX_CHARACTERS];
	long vlLeft[MAX_PLATES];
	long vlTop[MAX_PLATES];
	long vlRight[MAX_PLATES];
	long vlBottom[MAX_PLATES];
	long lProcessingTime;
	long vlFormat[MAX_PLATES];
	void* lUserParam1;
	void* lUserParam2;
	void* lUserParam3;
	void* lUserParam4;
	void* lUserParam5;
	char strPathCorrectedImage[MAX_FILE_PATH];
	long vlCharacterPosition[MAX_PLATES][MAX_CHARACTERS][4];


} tResults;


typedef struct _Region_
{
	long  left;	// Left coordinate of region within image (in pixels).
	long  top;		// Top coordinate of region within image (in pixels).
	long  right;	// Right coordinate of region within image (in pixels).
	long  bottom;	// Bottom coordinate of region within image (in pixels).
	long  ach;		// Approximate Average Character Height of region (in pixels).
} CandidateRegion;



// callback Client function executed to return the results once an image has been processed.
// typedef long __stdcall (* tCallbackResultados)(long messageCode, tResultados *resultados);

// Callback de resultats
typedef long (*callbackRes)(long code, tResults *resultados);


/////////////////////////////////////
// LIBRARY EXPORTED FUNCTIONS	   //
/////////////////////////////////////

#ifdef __cplusplus
extern "C" {
#endif


long  PREFIX(Init)(
							 callbackRes callbakc,
							  long lCountryCode,
							  long lAvCharacterHeight ,
							  bool bDuplicateLines ,
							  bool bReserved1 ,
							  long lReserved2 ,
							  bool bTrace );


void  PREFIX(End)(void);

long  PREFIX(Read)(
		tRecognitionEngineSettings *Configuration,
											long lWidth,
											long lHeight,
											unsigned char* pbImageData);
long  PREFIX(ReadCam)(
		tRecognitionEngineSettings *Configuration,
											long lWidth,
											long lHeight,
											unsigned char* pbImageData,
											int id_camera
											);


long  PREFIX(ReadRGB24)(
		tRecognitionEngineSettings *Configuration,
											long lWidth,
											long lHeight,
											unsigned char* pbImageData,
											bool bFlip = false
											);

long  PREFIX(ReadRGB24Cam)(
											tRecognitionEngineSettings *Configuration,
											long lWidth,
											long lHeight,
											unsigned char* pbImageData,
											int id_camera,
											bool bFlip);


long  PREFIX(ReadRGB32)(
		tRecognitionEngineSettings *Configuration,
											long lWidth,
											long lHeight,
											unsigned char* pbImageData,
											bool bFlip = false
											);

long  PREFIX(ReadRGB32Cam)(
											tRecognitionEngineSettings *Configuration,
											long lWidth,
											long lHeight,
											unsigned char* pbImageData,
											int id_camera,
											bool bFlip);


long  PREFIX(ReadBMP)(
		tRecognitionEngineSettings *Configuration,
											char * pcFilename);

long  PREFIX(ReadBMPCam)(
 											tRecognitionEngineSettings *Configuration,
 											char * pcFilename,int id_camera );


long  PREFIX(ReadJPG)(
		tRecognitionEngineSettings *Configuration,
											char * pcFilename);
long  PREFIX(ReadJPGCam)(
  											tRecognitionEngineSettings *Configuration,
  											char * pcFilename,int id_camera);





long  PREFIX(FindCandidateRegionsFromGreyscale)(long lWidth,
																							 long lHeight,
																							 unsigned char* pbImageData,
																							 long* plNumRegions,
																							 CandidateRegion* pRegions,
																							 long lMaxRegions,
																							 bool zPreciseCoordinates
																							 );



long  PREFIX(FindCandidateRegionsFromRGB24)(long lWidth,
																					     long lHeight,
																						 unsigned char* pbImageDataRGB,
																						 bool bFlip,
																						 long* plNumRegions,
																						 CandidateRegion* pRegions,
																						 long lMaxRegions,
																							 bool zPreciseCoordinates);



long  PREFIX(FindCandidateRegionsFromRGB32)(long lWidth,
																						 long lHeight,
																						 unsigned char* pbImageDataRGB,
																						 bool bFlip,
																						 long* plNumRegions,
																						 CandidateRegion* pRegions,
																						 long lMaxRegions,
																						 bool zPreciseCoordinates);

long  PREFIX(FindCandidateRegionsFromBMP)(char* strFilename,
																					   long* plNumRegions,
																					   CandidateRegion* pRegions,
																					   long lMaxRegions,
																					   bool zPreciseCoordinates);


long  PREFIX(FindCandidateRegionsFromJPG)(char* strFilename,
																					   long* plNumRegions,
																					   CandidateRegion* pRegions,
																					   long lMaxRegions,
																						bool zPreciseCoordinates);





long PREFIX(QueueSize)(void);

long FreeCores();

long NumLicenseCores();

long PREFIX(WriteHasp)(void* pData,long lSize);

long PREFIX(ReadHasp)(void* pData,long lSize);


long  PREFIX(SetCameraParameters)(int id_camera,long Threshold, double Tolerance);

void  PREFIX(ShowCameraMotionWindow)(int id_camera,bool show);


  bool   PREFIX(DetectMotion8)( long lWidth,
											long lHeight,
											unsigned char* pbImageData,
											int id_camera,int ROILEFT,int ROITOP,int ROIWIDTH,int ROIHEIGHT);
  bool   PREFIX(DetectMotion24)(long lWidth,
											long lHeight,
											unsigned char* pbImageData,
											int id_camera,int ROILEFT,int ROITOP,int ROIWIDTH,int ROIHEIGHT);
  bool   PREFIX(DetectMotion32)(long lWidth,
											long lHeight,
											unsigned char* pbImageData,
											int id_camera,int ROILEFT,int ROITOP,int ROIWIDTH,int ROIHEIGHT);

  bool   PREFIX(DetectMotionFile)(char* File,int id_camera,int ROILEFT,int ROITOP,int ROIWIDTH,int ROIHEIGHT);


  long  PREFIX(Read_sync)(
  											tRecognitionEngineSettings *Configuration,
  											long lWidth,
  											long lHeight,
  											unsigned char* pbImageData,
  											tResults &results);

  long  PREFIX(ReadRGB24_sync)(
  											tRecognitionEngineSettings *Configuration,
  											long lWidth,
  											long lHeight,
  											unsigned char* pbImageData,
  											tResults &results,
  											bool bFlip = false
  											);

  long  PREFIX(ReadRGB32_sync)(
  											tRecognitionEngineSettings *Configuration,
  											long lWidth,
  											long lHeight,
  											unsigned char* pbImageData,
  											tResults &results,
  											bool bFlip = false
  											);

    long  PREFIX(ReadBMP_sync)(
  											tRecognitionEngineSettings *Configuration,
  											char * pcFilename,
  											tResults &results);

    long  PREFIX(ReadJPG_sync)(
  											tRecognitionEngineSettings *Configuration,
  											char * pcFilename,
  											tResults &results);



long  PREFIX(QueueSize)(void);

#ifdef __cplusplus
}
#endif





#endif /* VPARMT_H_ */
