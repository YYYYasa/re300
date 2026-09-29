#include "HeroSpellVisual.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SceneComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Kismet/GameplayStatics.h"
#include "Camera/PlayerCameraManager.h"

AHeroSpellVisual::AHeroSpellVisual() {
    PrimaryActorTick.bCanEverTick=true;
    SetRootComponent(CreateDefaultSubobject<USceneComponent>(TEXT("SpellRoot")));
    SetActorEnableCollision(false);
}

void AHeroSpellVisual::AddLayer(const TCHAR* MaterialName,float Size) {
    auto Layer=NewObject<UStaticMeshComponent>(this);
    Layer->SetupAttachment(RootComponent);
    Layer->SetMobility(EComponentMobility::Movable);
    Layer->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Plane.Plane")));
    Layer->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Layer->SetCastShadow(false);
    const FString Path=FString::Printf(TEXT("/Game/Art/Heroes/H100/Effects/Materials/%s.%s"),MaterialName,MaterialName);
    auto Source=LoadObject<UMaterialInterface>(nullptr,*Path);
    auto Material=Source?UMaterialInstanceDynamic::Create(Source,this):nullptr;
    if(Material) {
        Layer->SetMaterial(0,Material);
        Material->SetScalarParameterValue(TEXT("Brightness"),bArea?2.2f:4.f);
    }
    Layer->SetRelativeScale3D(FVector(Size,Size,1));
    Layer->RegisterComponent();
    VisualLayers.Add(Layer);
    Materials.Add(Material);
}

void AHeroSpellVisual::Initialize(bool bAreaSpell) {
    bArea=bAreaSpell;
    Duration=bArea?1.25f:.5f;
    if(bArea) {
        AddLayer(TEXT("M_tx_kuosan_1027"),4.f);
        AddLayer(TEXT("M_tx_tuxing_0037"),2.5f);
        VisualLayers[1]->SetRelativeLocation(FVector(0,0,5));
        for(int32 I=0;I<8;++I) AddLayer(TEXT("M_tx_tuxing_1254"),1.f);
    } else AddLayer(TEXT("M_tx_xingguang_1013"),.7f);
    SetLifeSpan(Duration+.05f);
}

void AHeroSpellVisual::Tick(float DeltaTime) {
    Super::Tick(DeltaTime);
    Age+=DeltaTime;
    const float T=FMath::Clamp(Age/Duration,0.f,1.f);
    const float Fade=(1.f-FMath::SmoothStep(.35f,1.f,T))*FMath::Clamp(T*12.f,0.f,1.f);
    for(auto Material:Materials) if(Material) Material->SetScalarParameterValue(TEXT("Opacity"),Fade);
    if(VisualLayers.IsEmpty()) return;
    if(bArea) {
        VisualLayers[0]->SetRelativeScale3D(FVector(3.2f+T*3.6f,3.2f+T*3.6f,1));
        VisualLayers[0]->SetRelativeRotation(FRotator(0,T*85.f,0));
        VisualLayers[1]->SetRelativeRotation(FRotator(0,-T*140.f,0));
        for(int32 I=2;I<VisualLayers.Num();++I) {
            const float Angle=(I-2)*PI/4.f+T*1.2f;
            const float Radius=135.f+T*95.f;
            VisualLayers[I]->SetRelativeLocation(FVector(FMath::Cos(Angle)*Radius,FMath::Sin(Angle)*Radius,25.f+T*85.f));
            VisualLayers[I]->SetRelativeRotation(FRotator(0,FMath::RadiansToDegrees(Angle),0));
        }
    } else {
        if(auto Camera=UGameplayStatics::GetPlayerCameraManager(this,0))
            SetActorRotation(FRotationMatrix::MakeFromZ(Camera->GetCameraLocation()-GetActorLocation()).Rotator());
        VisualLayers[0]->SetRelativeScale3D(FVector(.5f+T*1.7f,.5f+T*1.7f,1));
    }
}

