#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/HUD.h"
#include "RebirthExperience.generated.h"

class UCameraComponent;
class UMaterialInstanceDynamic;
class UMaterialParameterCollection;
class APostProcessVolume;
class UAudioComponent;
class UInstancedStaticMeshComponent;

UCLASS()
class ETERNALREBIRTH_API ARebirthPawn : public APawn {
    GENERATED_BODY()
public:
    ARebirthPawn();
    virtual void BeginPlay() override;
    virtual void Tick(float Dt) override;
    virtual void SetupPlayerInputComponent(UInputComponent* Input) override;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UCameraComponent> Camera;
    UPROPERTY() TObjectPtr<UMaterialInstanceDynamic> AnimePost;
    UPROPERTY() TObjectPtr<APostProcessVolume> PostVolume;
    UPROPERTY() TObjectPtr<UMaterialParameterCollection> StyleParameters;
    UPROPERTY() TObjectPtr<UMaterialParameterCollection> WeatherParameters;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UInstancedStaticMeshComponent> RainInstances;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UInstancedStaticMeshComponent> SnowInstances;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UAudioComponent> ClearAudio;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UAudioComponent> RainAudio;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UAudioComponent> SnowAudio;
    bool bAnime=false, bTour=false, bShowHUD=true, bUltra=true;
    float Blend=0, TourTime=0, Elapsed=0;
    float Wetness=0, SnowCover=0, RainVisual=0, SnowVisual=0;
    int32 WeatherIndex=0;
    int32 ViewIndex=0;
    FString GetViewName() const;
    FString GetWeatherName() const;
    void SetView(int32 Index);
    void ToggleStyle();
    void ApplyStyle();
    void ToggleTour();
    void ToggleHUD();
    void Photo();
    void ToggleQuality();
    void ToggleWeather();
private:
    FVector MoveInput=FVector::ZeroVector;
    void Forward(float V); void Right(float V); void Up(float V);
    void LookX(float V); void LookY(float V);
    void View1(); void View2(); void View3(); void View4(); void View5();
    void Quit();
    void SetWeather(int32 Index);
    void UpdateWeather(float Dt);
    void UpdatePrecipitation(float Dt);
    bool bCaptureRun=false, bCaptureAnime=false, bStyleTest=false, bGallery=false, bMotionTest=false, bWeatherTest=false;
    int32 CaptureStage=0, GalleryIndex=0, GalleryPrepared=0;
    int32 WeatherTestStage=0;
    TArray<FVector> RainOffsets, SnowOffsets;
    TArray<float> RainSpeeds, SnowSpeeds;
};

UCLASS()
class ETERNALREBIRTH_API ARebirthHUD : public AHUD {
    GENERATED_BODY()
public:
    virtual void DrawHUD() override;
};

UCLASS()
class ETERNALREBIRTH_API ARebirthGameMode : public AGameModeBase {
    GENERATED_BODY()
public:
    ARebirthGameMode();
};
