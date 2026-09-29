#include "RebirthExperience.h"
#include "Camera/CameraComponent.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "Engine/PostProcessVolume.h"
#include "Engine/DirectionalLight.h"
#include "Engine/SkyLight.h"
#include "Engine/PointLight.h"
#include "Engine/ExponentialHeightFog.h"
#include "Components/DirectionalLightComponent.h"
#include "Components/SkyLightComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/ExponentialHeightFogComponent.h"
#include "Components/AudioComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialParameterCollection.h"
#include "Materials/MaterialInterface.h"
#include "Engine/StaticMesh.h"
#include "Animation/SkeletalMeshActor.h"
#include "Components/SkeletalMeshComponent.h"
#include "Animation/AnimSequence.h"
#include "Sound/SoundBase.h"
#include "Math/RotationMatrix.h"
#include "Kismet/KismetMaterialLibrary.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "HAL/IConsoleManager.h"
#include "Misc/CommandLine.h"
#include "Misc/Paths.h"
#include "Misc/FileHelper.h"
#include "UnrealClient.h"
#include "Kismet/GameplayStatics.h"

ARebirthPawn::ARebirthPawn() {
    PrimaryActorTick.bCanEverTick=true;
    RootComponent=CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
    Camera=CreateDefaultSubobject<UCameraComponent>(TEXT("Camera"));
    Camera->SetupAttachment(RootComponent); Camera->FieldOfView=65;
    RainInstances=CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("RainParticles"));
    RainInstances->SetupAttachment(RootComponent);
    RainInstances->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    RainInstances->SetMobility(EComponentMobility::Movable);
    RainInstances->CastShadow=false;
    RainInstances->SetVisibility(false);
    SnowInstances=CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("SnowParticles"));
    SnowInstances->SetupAttachment(RootComponent);
    SnowInstances->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    SnowInstances->SetMobility(EComponentMobility::Movable);
    SnowInstances->CastShadow=false;
    SnowInstances->SetVisibility(false);
    ClearAudio=CreateDefaultSubobject<UAudioComponent>(TEXT("ClearAmbience"));
    RainAudio=CreateDefaultSubobject<UAudioComponent>(TEXT("RainAmbience"));
    SnowAudio=CreateDefaultSubobject<UAudioComponent>(TEXT("SnowAmbience"));
    for(UAudioComponent* Audio : {ClearAudio.Get(),RainAudio.Get(),SnowAudio.Get()}) {
        Audio->SetupAttachment(RootComponent);
        Audio->bAutoActivate=false;
    }
    AutoPossessPlayer=EAutoReceiveInput::Player0;
}

void ARebirthPawn::BeginPlay() {
    Super::BeginPlay();
    if (auto PC=Cast<APlayerController>(Controller)) { PC->bShowMouseCursor=false; PC->SetInputMode(FInputModeGameOnly()); }
    TActorIterator<APostProcessVolume> PostIt(GetWorld());
    if(PostIt) PostVolume=*PostIt;
    StyleParameters=LoadObject<UMaterialParameterCollection>(nullptr,TEXT("/Game/Art/Materials/MPC_Style.MPC_Style"));
    WeatherParameters=LoadObject<UMaterialParameterCollection>(nullptr,TEXT("/Game/Art/Materials/MPC_Weather.MPC_Weather"));
    if(auto Mat=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/Art/Materials/M_AnimePost.M_AnimePost"))) {
        AnimePost=UMaterialInstanceDynamic::Create(Mat,this);
        Camera->PostProcessSettings.AddBlendable(AnimePost,1);
        Camera->PostProcessBlendWeight=1;
    }
    bCaptureRun=FParse::Param(FCommandLine::Get(),TEXT("RebirthCapture"));
    bCaptureAnime=FParse::Param(FCommandLine::Get(),TEXT("Anime"));
    bStyleTest=FParse::Param(FCommandLine::Get(),TEXT("RebirthStyleTest"));
    bGallery=FParse::Param(FCommandLine::Get(),TEXT("RebirthGallery"));
    bMotionTest=FParse::Param(FCommandLine::Get(),TEXT("RebirthMotionTest"));
    bWeatherTest=FParse::Param(FCommandLine::Get(),TEXT("RebirthWeatherTest"));
    int32 StartView=1; FParse::Value(FCommandLine::Get(),TEXT("RebirthView="),StartView);
    bAnime=bCaptureAnime; SetView(FMath::Clamp(StartView-1,0,4));
    if(bGallery){bAnime=false;SetView(0);}
    if(FParse::Param(FCommandLine::Get(),TEXT("RebirthWaterCloseup"))) {
        const FVector Eye(3000,3500,180), Target(1500,1500,25);
        SetActorLocationAndRotation(Eye,(Target-Eye).Rotation());
    }
    if(auto Plane=LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Plane.Plane"))) {
        RainInstances->SetStaticMesh(Plane);
        SnowInstances->SetStaticMesh(Plane);
    }
    if(auto RainMat=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/Art/Materials/M_RainStreak.M_RainStreak")))RainInstances->SetMaterial(0,RainMat);
    if(auto SnowMat=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/Art/Materials/M_SnowFlake.M_SnowFlake")))SnowInstances->SetMaterial(0,SnowMat);
    FRandomStream Random(30058);
    for(int32 I=0;I<1800;I++) {
        FVector Offset(Random.FRandRange(-1100,1100),Random.FRandRange(-1100,1100),Random.FRandRange(-500,1000));
        RainOffsets.Add(Offset);
        RainSpeeds.Add(Random.FRandRange(1450,2100));
        RainInstances->AddInstance(FTransform(FRotator::ZeroRotator,GetActorLocation()+Offset,FVector(.010f,.24f,1)),true);
    }
    for(int32 I=0;I<1000;I++) {
        FVector Offset(Random.FRandRange(-1400,1400),Random.FRandRange(-1400,1400),Random.FRandRange(-550,1100));
        SnowOffsets.Add(Offset);
        SnowSpeeds.Add(Random.FRandRange(75,190));
        const float Size=Random.FRandRange(.035f,.095f);
        SnowInstances->AddInstance(FTransform(FRotator::ZeroRotator,GetActorLocation()+Offset,FVector(Size,Size,1)),true);
    }
    const TCHAR* SoundPaths[]={TEXT("/Game/Art/Audio/ClearWeatherLoop.ClearWeatherLoop"),TEXT("/Game/Art/Audio/RainWeatherLoop.RainWeatherLoop"),TEXT("/Game/Art/Audio/SnowWeatherLoop.SnowWeatherLoop")};
    UAudioComponent* AudioComponents[]={ClearAudio.Get(),RainAudio.Get(),SnowAudio.Get()};
    for(int32 I=0;I<3;I++)if(auto Sound=LoadObject<USoundBase>(nullptr,SoundPaths[I])) {
        AudioComponents[I]->SetSound(Sound);
        AudioComponents[I]->SetVolumeMultiplier(0);
        AudioComponents[I]->Play();
    }
    FString InitialWeather;
    if(FParse::Value(FCommandLine::Get(),TEXT("RebirthWeather="),InitialWeather)) {
        if(InitialWeather.Equals(TEXT("Rain"),ESearchCase::IgnoreCase))SetWeather(1);
        else if(InitialWeather.Equals(TEXT("Snow"),ESearchCase::IgnoreCase))SetWeather(2);
    }
    ApplyStyle();
    for(TActorIterator<ASkeletalMeshActor> It(GetWorld());It;++It) {
        if(!It->ActorHasTag(TEXT("ImportedHero")))continue;
        for(const TCHAR* HeroId : {TEXT("013"),TEXT("100"),TEXT("101")}) {
            if(!It->ActorHasTag(FName(*FString::Printf(TEXT("Hero%s"),HeroId))))continue;
            const FString Path=FString::Printf(TEXT("/Game/Art/Heroes/H%s/AN_H%s_Idle.AN_H%s_Idle"),HeroId,HeroId,HeroId);
            if(auto Animation=LoadObject<UAnimSequence>(nullptr,*Path)) {
                It->GetSkeletalMeshComponent()->PlayAnimation(Animation,true);
                UE_LOG(LogTemp,Display,TEXT("REBIRTH_HERO_PLAY id=%s animation=%s"),HeroId,*Path);
            }
        }
    }
    UE_LOG(LogTemp,Display,TEXT("REBIRTH_READY style=%s view=%d"),bAnime?TEXT("anime"):TEXT("realistic"),ViewIndex+1);
}

void ARebirthPawn::SetupPlayerInputComponent(UInputComponent* I) {
    Super::SetupPlayerInputComponent(I);
    I->BindAxis("Forward",this,&ARebirthPawn::Forward); I->BindAxis("Right",this,&ARebirthPawn::Right); I->BindAxis("Up",this,&ARebirthPawn::Up);
    I->BindAxis("LookX",this,&ARebirthPawn::LookX); I->BindAxis("LookY",this,&ARebirthPawn::LookY);
    I->BindAction("Style",IE_Pressed,this,&ARebirthPawn::ToggleStyle); I->BindAction("Tour",IE_Pressed,this,&ARebirthPawn::ToggleTour);
    I->BindAction("HUD",IE_Pressed,this,&ARebirthPawn::ToggleHUD); I->BindAction("Photo",IE_Pressed,this,&ARebirthPawn::Photo);
    I->BindAction("Quality",IE_Pressed,this,&ARebirthPawn::ToggleQuality); I->BindAction("Quit",IE_Pressed,this,&ARebirthPawn::Quit);
    I->BindAction("Weather",IE_Pressed,this,&ARebirthPawn::ToggleWeather);
    I->BindAction("View1",IE_Pressed,this,&ARebirthPawn::View1); I->BindAction("View2",IE_Pressed,this,&ARebirthPawn::View2);
    I->BindAction("View3",IE_Pressed,this,&ARebirthPawn::View3); I->BindAction("View4",IE_Pressed,this,&ARebirthPawn::View4); I->BindAction("View5",IE_Pressed,this,&ARebirthPawn::View5);
}
void ARebirthPawn::Forward(float V){MoveInput.X=V;} void ARebirthPawn::Right(float V){MoveInput.Y=V;} void ARebirthPawn::Up(float V){MoveInput.Z=V;}
void ARebirthPawn::LookX(float V){if(!bTour && FMath::Abs(V)>0.001)AddActorWorldRotation(FRotator(0,V*1.5f,0));}
void ARebirthPawn::LookY(float V){if(!bTour){auto R=GetActorRotation();R.Pitch=FMath::Clamp(R.Pitch+V*1.5f,-85.f,85.f);SetActorRotation(R);}}
void ARebirthPawn::View1(){SetView(0);} void ARebirthPawn::View2(){SetView(1);} void ARebirthPawn::View3(){SetView(2);} void ARebirthPawn::View4(){SetView(3);} void ARebirthPawn::View5(){SetView(4);}
FString ARebirthPawn::GetViewName()const {
    const TCHAR* Names[]={TEXT("THE ETERNAL ARENA"),TEXT("SAPPHIRE SANCTUM"),TEXT("RIVER OF WORLDS"),TEXT("CRIMSON CITADEL"),TEXT("THE ANCIENT WILD")};
    return Names[FMath::Clamp(ViewIndex,0,4)];
}
FString ARebirthPawn::GetWeatherName()const {
    const TCHAR* Names[]={TEXT("CLEAR"),TEXT("RAIN"),TEXT("SNOW")};
    return Names[FMath::Clamp(WeatherIndex,0,2)];
}
void ARebirthPawn::SetView(int32 Index) {
    bTour=false; ViewIndex=Index;
    FName Tag(*FString::Printf(TEXT("View%d"),Index+1));
    for(TActorIterator<AActor> It(GetWorld());It;++It) if(It->ActorHasTag(Tag)) { SetActorLocationAndRotation(It->GetActorLocation(),It->GetActorRotation()); return; }
    SetActorLocationAndRotation(FVector(-10000,-10000,14000),FRotator(-40,45,0));
}
void ARebirthPawn::ToggleStyle(){bAnime=!bAnime;ApplyStyle();UE_LOG(LogTemp,Display,TEXT("REBIRTH_STYLE %s"),bAnime?TEXT("anime"):TEXT("realistic"));}
void ARebirthPawn::ToggleTour(){bTour=!bTour;TourTime=0;}
void ARebirthPawn::ToggleHUD(){bShowHUD=!bShowHUD;}
void ARebirthPawn::Photo(){FScreenshotRequest::RequestScreenshot(FPaths::ProjectSavedDir()/TEXT("Screenshots")/(bAnime?TEXT("Anime.png"):TEXT("Realistic.png")),false,true);}
void ARebirthPawn::ToggleQuality(){bUltra=!bUltra;if(auto V=IConsoleManager::Get().FindConsoleVariable(TEXT("r.ScreenPercentage")))V->Set(bUltra?100.f:75.f,ECVF_SetByCode);}
void ARebirthPawn::ToggleWeather(){SetWeather((WeatherIndex+1)%3);}
void ARebirthPawn::SetWeather(int32 Index){
    WeatherIndex=FMath::Clamp(Index,0,2);
    UE_LOG(LogTemp,Display,TEXT("REBIRTH_WEATHER %s wet=%.2f snow=%.2f"),*GetWeatherName(),Wetness,SnowCover);
}
void ARebirthPawn::Quit(){if(auto PC=Cast<APlayerController>(Controller))PC->ConsoleCommand(TEXT("quit"));}

void ARebirthPawn::UpdateWeather(float Dt) {
    RainVisual=FMath::FInterpConstantTo(RainVisual,WeatherIndex==1?1.f:0.f,Dt,.48f);
    SnowVisual=FMath::FInterpConstantTo(SnowVisual,WeatherIndex==2?1.f:0.f,Dt,.36f);
    Wetness=FMath::FInterpConstantTo(Wetness,WeatherIndex==1?1.f:0.f,Dt,WeatherIndex==1?.07f:.05f);
    SnowCover=FMath::FInterpConstantTo(SnowCover,WeatherIndex==2?1.f:0.f,Dt,WeatherIndex==2?.055f:.045f);
    if(WeatherParameters) {
        UKismetMaterialLibrary::SetScalarParameterValue(this,WeatherParameters,TEXT("Wetness"),Wetness);
        UKismetMaterialLibrary::SetScalarParameterValue(this,WeatherParameters,TEXT("SnowCover"),SnowCover);
        UKismetMaterialLibrary::SetScalarParameterValue(this,WeatherParameters,TEXT("RainAmount"),RainVisual);
        UKismetMaterialLibrary::SetScalarParameterValue(this,WeatherParameters,TEXT("SnowAmount"),SnowVisual);
    }
    for(TActorIterator<ADirectionalLight> It(GetWorld());It;++It) {
        auto Light=Cast<UDirectionalLightComponent>(It->GetLightComponent());
        const float Base=bAnime?4.2f:4.7f;
        Light->SetIntensity(Base*(1-.72f*RainVisual-.55f*SnowVisual));
        Light->SetLightColor(FLinearColor(1.f,.92f-.12f*RainVisual-.05f*SnowVisual,.80f+.13f*SnowVisual));
    }
    for(TActorIterator<ASkyLight> It(GetWorld());It;++It) {
        auto Light=It->GetLightComponent();
        Light->SetIntensity((bAnime?1.3f:2.f)*(1-.26f*RainVisual-.10f*SnowVisual));
    }
    for(TActorIterator<AExponentialHeightFog> It(GetWorld());It;++It) {
        It->GetComponent()->SetFogDensity((bAnime?.0035f:.006f)+.008f*RainVisual+.006f*SnowVisual);
        It->GetComponent()->SetFogInscatteringColor(FLinearColor(.45f-.11f*RainVisual+.12f*SnowVisual,
            .54f-.07f*RainVisual+.10f*SnowVisual,.60f+.08f*SnowVisual));
    }
    for(TActorIterator<APointLight> It(GetWorld());It;++It)if(It->ActorHasTag(TEXT("RebirthFill"))) {
        It->GetLightComponent()->SetVolumetricScatteringIntensity(1.35f*(1-.72f*RainVisual-.45f*SnowVisual));
    }
    if(PostVolume) {
        auto& S=PostVolume->Settings;
        S.bOverride_ColorSaturation=true;
        const float Saturation=(bAnime?1.14f:1.f)*(1-.20f*RainVisual-.13f*SnowVisual);
        S.ColorSaturation=FVector4(1,1,1,Saturation);
        S.bOverride_BloomIntensity=true;
        S.BloomIntensity=(bAnime?.20f:.32f)*(1-.35f*RainVisual);
    }
    if(ClearAudio)ClearAudio->SetVolumeMultiplier(.34f*(1-FMath::Max(RainVisual,SnowVisual)));
    if(RainAudio)RainAudio->SetVolumeMultiplier(.78f*RainVisual);
    if(SnowAudio)SnowAudio->SetVolumeMultiplier(.58f*SnowVisual);
    RainInstances->SetVisibility(RainVisual>.005f);
    SnowInstances->SetVisibility(SnowVisual>.005f);
}

void ARebirthPawn::UpdatePrecipitation(float Dt) {
    const FRotator Facing=FRotationMatrix::MakeFromZY(-Camera->GetForwardVector(),FVector::UpVector).Rotator();
    if(RainVisual>.005f) {
        for(int32 I=0;I<RainOffsets.Num();I++) {
            FVector& P=RainOffsets[I];
            P.Z-=RainSpeeds[I]*Dt;
            P.X+=125.f*Dt;
            if(P.Z < -500.f){P.Z+=1500.f;P.X=FMath::FRandRange(-1100.f,1100.f);P.Y=FMath::FRandRange(-1100.f,1100.f);}
            if(P.X>1100.f)P.X-=2200.f;
            RainInstances->UpdateInstanceTransform(I,FTransform(Facing,GetActorLocation()+P,FVector(.010f,.24f,1)),true,I==RainOffsets.Num()-1,true);
        }
    }
    if(SnowVisual>.005f) {
        for(int32 I=0;I<SnowOffsets.Num();I++) {
            FVector& P=SnowOffsets[I];
            P.Z-=SnowSpeeds[I]*Dt;
            P.X+=(28.f+10.f*FMath::Sin(Elapsed*.6f+I*.27f))*Dt;
            if(P.Z < -550.f){P.Z+=1650.f;P.X=FMath::FRandRange(-1400.f,1400.f);P.Y=FMath::FRandRange(-1400.f,1400.f);}
            if(P.X>1400.f)P.X-=2800.f;
            const float Size=.045f+.03f*FMath::Frac(I*.6180339f);
            SnowInstances->UpdateInstanceTransform(I,FTransform(Facing,GetActorLocation()+P,FVector(Size,Size,1)),true,I==SnowOffsets.Num()-1,true);
        }
    }
}

void ARebirthPawn::ApplyStyle() {
    for(TActorIterator<ADirectionalLight> It(GetWorld());It;++It) {
        auto L=Cast<UDirectionalLightComponent>(It->GetLightComponent());
        L->SetIntensity(bAnime?4.2f:4.7f);
        L->SetLightColor(bAnime?FLinearColor(1,.94f,.87f):FLinearColor(1,.92f,.80f));
        L->SetLightSourceAngle(bAnime?3.f:8.f);
        L->SetShadowAmount(bAnime?.82f:.58f);
        It->SetActorRotation(bAnime?FRotator(-48,-35,0):FRotator(-49,-32,0));
    }
    for(TActorIterator<ASkyLight> It(GetWorld());It;++It) {
        It->GetLightComponent()->SetIntensity(bAnime?1.3f:2.0f);
        It->GetLightComponent()->SetLightColor(bAnime?FLinearColor(.68f,.83f,1):FLinearColor(.85f,.91f,1));
    }
    for(TActorIterator<AExponentialHeightFog> It(GetWorld());It;++It) {
        It->GetComponent()->SetFogDensity(bAnime?.0035f:.006f);
        It->GetComponent()->SetFogInscatteringColor(bAnime?FLinearColor(.40f,.66f,.88f):FLinearColor(.45f,.54f,.60f));
    }
    if(PostVolume) {
        auto& S=PostVolume->Settings;
        S.bOverride_BloomIntensity=true; S.BloomIntensity=bAnime?.20f:.32f;
        S.bOverride_VignetteIntensity=true; S.VignetteIntensity=bAnime?.10f:.13f;
        S.bOverride_ColorSaturation=true; S.ColorSaturation=FVector4(1.f,1.f,1.f,bAnime?1.14f:1.f);
        S.bOverride_ColorContrast=true; S.ColorContrast=FVector4(1.f,1.f,1.f,bAnime?1.02f:1.01f);
        S.bOverride_AmbientOcclusionIntensity=true; S.AmbientOcclusionIntensity=bAnime?.35f:.20f;
    }
}

void ARebirthPawn::Tick(float Dt) {
    Super::Tick(Dt); Elapsed+=Dt;
    Blend=FMath::FInterpTo(Blend,bAnime?1.f:0.f,Dt,4.f);
    if(AnimePost) AnimePost->SetScalarParameterValue(TEXT("AnimeMix"),Blend);
    if(StyleParameters) UKismetMaterialLibrary::SetScalarParameterValue(this,StyleParameters,TEXT("AnimeMix"),Blend);
    UpdateWeather(Dt);
    UpdatePrecipitation(Dt);
    if(bTour) {
        TourTime+=Dt;
        const float A=TourTime*.018f+.7f;
        FVector P(FMath::Cos(A)*16000,FMath::Sin(A)*16000,11000+1500*FMath::Sin(A*.7f));
        SetActorLocationAndRotation(P,(FVector(0,0,200)-P).Rotation());
    } else if(!MoveInput.IsNearlyZero()) {
        auto PC=Cast<APlayerController>(Controller);
        float Speed=(PC && PC->IsInputKeyDown(EKeys::LeftShift))?6500.f:1800.f;
        FVector V=GetActorForwardVector()*MoveInput.X+GetActorRightVector()*MoveInput.Y+FVector::UpVector*MoveInput.Z;
        FVector P=GetActorLocation()+V.GetClampedToMaxSize(1)*Speed*Dt;
        P.X=FMath::Clamp(P.X,-35000.,35000.);P.Y=FMath::Clamp(P.Y,-35000.,35000.);P.Z=FMath::Clamp(P.Z,100.,35000.);
        SetActorLocation(P);
    }
    if(bGallery) {
        if(GalleryIndex<10 && GalleryPrepared==GalleryIndex && Elapsed>20+GalleryIndex*10) {
            bShowHUD=!FParse::Param(FCommandLine::Get(),TEXT("Clean"));
            FScreenshotRequest::RequestScreenshot(FPaths::ProjectSavedDir()/TEXT("Screenshots")/FString::Printf(TEXT("%s_View%d.png"),bAnime?TEXT("Anime"):TEXT("Realistic"),ViewIndex+1),false,false);
            GalleryIndex++;
        }
        if(GalleryIndex<10 && GalleryPrepared<GalleryIndex && Elapsed>22+(GalleryIndex-1)*10) {
            SetView(GalleryIndex/2); bAnime=GalleryIndex%2!=0; ApplyStyle(); GalleryPrepared=GalleryIndex;
        }
        if(Elapsed>114)Quit();
    }
    if(bCaptureRun && !bGallery && Elapsed>18 && CaptureStage==0) {
        bShowHUD=!FParse::Param(FCommandLine::Get(),TEXT("Clean"));
        const bool bHeroPreview=FParse::Param(FCommandLine::Get(),TEXT("RebirthHeroGallery"));
        const FString Filename=bHeroPreview?FString::Printf(TEXT("Hero_%s.png"),bAnime?TEXT("Anime"):TEXT("Realistic")):FString::Printf(TEXT("%s_View%d.png"),bAnime?TEXT("Anime"):TEXT("Realistic"),ViewIndex+1);
        FScreenshotRequest::RequestScreenshot(FPaths::ProjectSavedDir()/TEXT("Screenshots")/Filename,false,false);
        CaptureStage=1;
    }
    if(bStyleTest && Elapsed>20 && CaptureStage==1){ToggleStyle();CaptureStage=2;}
    if(bMotionTest && Elapsed>22 && CaptureStage==1){
        FScreenshotRequest::RequestScreenshot(FPaths::ProjectSavedDir()/TEXT("Screenshots")/FString::Printf(TEXT("Motion_View%d.png"),ViewIndex+1),false,false);
        CaptureStage=2;
    }
    if(bStyleTest && Elapsed>28 && CaptureStage==2){
        FScreenshotRequest::RequestScreenshot(FPaths::ProjectSavedDir()/TEXT("Screenshots/StyleToggle.png"),false,false);CaptureStage=3;
        int32 ViewCount=0;
        for(TActorIterator<AActor> It(GetWorld());It;++It)
            for(int32 V=1;V<=5;V++)if(It->ActorHasTag(FName(*FString::Printf(TEXT("View%d"),V))))ViewCount++;
        const bool Passed=AnimePost && StyleParameters && ViewCount==5 && bAnime!=bCaptureAnime && FMath::Abs(Blend-(bAnime?1.f:0.f))<.01f;
        FFileHelper::SaveStringToFile(FString::Printf(TEXT("{\"passed\":%s,\"styleToggle\":%s,\"anime\":%s,\"view\":%d,\"viewpoints\":%d,\"styleBlend\":%.4f}"),Passed?TEXT("true"):TEXT("false"),bAnime!=bCaptureAnime?TEXT("true"):TEXT("false"),bAnime?TEXT("true"):TEXT("false"),ViewIndex+1,ViewCount,Blend),*(FPaths::ProjectSavedDir()/TEXT("smoke-test.json")));
    }
    if(bCaptureRun && !bGallery && Elapsed>(bStyleTest?33:(bMotionTest?28:23)))Quit();
    if(bWeatherTest) {
        bShowHUD=!FParse::Param(FCommandLine::Get(),TEXT("Clean"));
        auto Shot=[this](const TCHAR* Name){FScreenshotRequest::RequestScreenshot(FPaths::ProjectSavedDir()/TEXT("Screenshots")/Name,false,false);};
        if(WeatherTestStage==0 && Elapsed>2){SetWeather(1);WeatherTestStage=1;}
        if(WeatherTestStage==1 && Elapsed>8){Shot(TEXT("Weather_RainGrowing.png"));WeatherTestStage=2;}
        if(WeatherTestStage==2 && Elapsed>19){Shot(TEXT("Weather_RainFull.png"));SetWeather(2);WeatherTestStage=3;}
        if(WeatherTestStage==3 && Elapsed>27){Shot(TEXT("Weather_SnowGrowing.png"));WeatherTestStage=4;}
        if(WeatherTestStage==4 && Elapsed>43){Shot(TEXT("Weather_SnowFull.png"));SetWeather(0);WeatherTestStage=5;}
        if(WeatherTestStage==5 && Elapsed>50){Shot(TEXT("Weather_ClearRecovery.png"));WeatherTestStage=6;}
        if(WeatherTestStage==6 && Elapsed>69){
            Shot(TEXT("Weather_ClearRestored.png"));WeatherTestStage=7;
            const bool AudioReady=ClearAudio && ClearAudio->Sound && RainAudio && RainAudio->Sound && SnowAudio && SnowAudio->Sound;
            const bool ParticlesReady=RainInstances && RainInstances->GetMaterial(0) && SnowInstances && SnowInstances->GetMaterial(0);
            const bool Passed=WeatherParameters && AudioReady && ParticlesReady && Wetness<.02f && SnowCover<.02f && WeatherIndex==0;
            FFileHelper::SaveStringToFile(FString::Printf(TEXT("{\"passed\":%s,\"weather\":\"clear\",\"wetness\":%.3f,\"snowCover\":%.3f,\"rainParticles\":%d,\"snowParticles\":%d}"),Passed?TEXT("true"):TEXT("false"),Wetness,SnowCover,RainOffsets.Num(),SnowOffsets.Num()),*(FPaths::ProjectSavedDir()/TEXT("weather-test.json")));
        }
        if(Elapsed>72)Quit();
    }
}

ARebirthGameMode::ARebirthGameMode(){DefaultPawnClass=ARebirthPawn::StaticClass();HUDClass=ARebirthHUD::StaticClass();}

void ARebirthHUD::DrawHUD() {
    Super::DrawHUD();
    auto P=Cast<ARebirthPawn>(UGameplayStatics::GetPlayerPawn(GetWorld(),0));
    if(!Canvas || !P || !P->bShowHUD)return;
    const float W=Canvas->SizeX,H=Canvas->SizeY, S=FMath::Max(.75f,W/1920.f), M=44*S;
    FLinearColor White(.9f,.94f,.96f,1),Muted(.55f,.66f,.72f,1),Accent=P->bAnime?FLinearColor(1,.63f,.70f):FLinearColor(.37f,.89f,.9f);
    DrawRect(FLinearColor(.012f,.023f,.04f,.78f),M-16*S,30*S,350*S,120*S);
    DrawRect(Accent,M-16*S,30*S,3*S,120*S);
    DrawText(TEXT("300  /  ETERNAL REBIRTH"),White,M,45*S,GEngine->GetMediumFont(),1.0f*S,false);
    DrawText(TEXT("A WORLD WORTH RETURNING TO"),Muted,M,81*S,GEngine->GetSmallFont(),.9f*S,false);
    DrawText(P->GetViewName(),Accent,M,115*S,GEngine->GetSmallFont(),.95f*S,false);
    float RX=W-355*S;
    DrawRect(FLinearColor(.012f,.023f,.04f,.80f),RX,30*S,310*S,115*S);
    DrawText(P->bAnime?TEXT("02   MODERN ANIME"):TEXT("01   CINEMATIC REALISM"),White,RX+17*S,43*S,GEngine->GetSmallFont(),1.12f*S,false);
    DrawText(TEXT("TAB  /  SWITCH THE ATMOSPHERE"),Accent,RX+17*S,72*S,GEngine->GetSmallFont(),.80f*S,false);
    DrawText(FString::Printf(TEXT("F  /  WEATHER : %s"),*P->GetWeatherName()),White,RX+17*S,96*S,GEngine->GetSmallFont(),.95f*S,false);
    DrawText(FString::Printf(TEXT("WET %02d%%   SNOW %02d%%"),FMath::RoundToInt(P->Wetness*100),FMath::RoundToInt(P->SnowCover*100)),Muted,RX+17*S,121*S,GEngine->GetSmallFont(),.78f*S,false);
    DrawRect(FLinearColor(.012f,.023f,.04f,.78f),M-16*S,H-80*S,W-2*M+32*S,45*S);
    DrawText(TEXT("W A S D  Move    MOUSE  Look    Q / E  Height    SHIFT  Boost    1 - 5  Vistas    F  Weather    G  Quality    T  Tour    H  Hide    F9  Photo    ESC  Exit"),White,M,H-65*S,GEngine->GetSmallFont(),.83f*S,false);
    DrawText(P->bTour?TEXT("GUIDED FLIGHT"):TEXT("FREE EXPLORATION"),Muted,M,H-111*S,GEngine->GetSmallFont(),.90f*S,false);
    DrawText(P->bUltra?TEXT("G  /  NATIVE QUALITY"):TEXT("G  /  BALANCED QUALITY"),Muted,W-283*S,H-111*S,GEngine->GetSmallFont(),.85f*S,false);
}
