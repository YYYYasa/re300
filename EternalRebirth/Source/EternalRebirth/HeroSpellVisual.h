#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "HeroSpellVisual.generated.h"

class UStaticMeshComponent;
class UMaterialInstanceDynamic;

UCLASS()
class ETERNALREBIRTH_API AHeroSpellVisual : public AActor {
    GENERATED_BODY()
public:
    AHeroSpellVisual();
    void Initialize(bool bAreaSpell);
    virtual void Tick(float DeltaTime) override;
private:
    UPROPERTY() TArray<TObjectPtr<UStaticMeshComponent>> VisualLayers;
    UPROPERTY() TArray<TObjectPtr<UMaterialInstanceDynamic>> Materials;
    bool bArea=false;
    float Age=0.f, Duration=.55f;
    void AddLayer(const TCHAR* MaterialName, float Size);
};

