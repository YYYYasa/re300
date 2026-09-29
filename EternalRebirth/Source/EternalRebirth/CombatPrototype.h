#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/Actor.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/HUD.h"
#include "CombatPrototype.generated.h"

class UCapsuleComponent;
class USkeletalMeshComponent;
class USpringArmComponent;
class UCameraComponent;
class UAnimSequence;
class UBlendSpace1D;
class UMaterialInstanceDynamic;
class UMaterialParameterCollection;
class APostProcessVolume;
class UTexture2D;
class UStaticMeshComponent;

UCLASS()
class ETERNALREBIRTH_API ACombatTrainingDummy : public AActor {
    GENERATED_BODY()
public:
    ACombatTrainingDummy();
    virtual void BeginPlay() override;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UCapsuleComponent> Capsule;
    UPROPERTY(VisibleAnywhere) TObjectPtr<USkeletalMeshComponent> Mesh;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Combat") float MaxHealth=600.f;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Combat") float Health=600.f;
    float LastDamage=0.f;
    float LastHitTime=-100.f;
    bool ReceiveDamage(float Amount);
    void ResetDummy();
private:
    FTimerHandle ResetTimer;
};

UCLASS()
class ETERNALREBIRTH_API ACombatHeroPawn : public APawn {
    GENERATED_BODY()
public:
    ACombatHeroPawn();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaTime) override;
    virtual void SetupPlayerInputComponent(UInputComponent* Input) override;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UCapsuleComponent> Capsule;
    UPROPERTY(VisibleAnywhere) TObjectPtr<USkeletalMeshComponent> Mesh;
    UPROPERTY(VisibleAnywhere) TObjectPtr<USpringArmComponent> CameraBoom;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UCameraComponent> Camera;
    UPROPERTY(BlueprintReadOnly, Category="Combat") float Health=1000.f;
    UPROPERTY(BlueprintReadOnly, Category="Combat") float MaxHealth=1000.f;
    float AttackCooldownRemaining() const;
    float SkillCooldownRemaining() const;
    float ZoomDistance() const { return DesiredCameraDistance; }
    float MoveSpeedAlpha() const { return LocomotionAlpha; }
    bool HasMoveDestination() const { return bHasMoveDestination; }
    FVector GetMoveDestination() const { return MoveDestination; }
    ACombatTrainingDummy* GetTarget() const { return Target.Get(); }
    bool IsAnimeStyle() const { return bAnimeStyle; }
    bool IsShowcaseBattle() const { return bShowcaseBattle; }
private:
    UPROPERTY() TObjectPtr<UAnimSequence> IdleAnimation;
    UPROPERTY() TObjectPtr<UAnimSequence> RunAnimation;
    UPROPERTY() TObjectPtr<UAnimSequence> AttackAnimation;
    UPROPERTY() TObjectPtr<UAnimSequence> AttackAnimation2;
    UPROPERTY() TObjectPtr<UAnimSequence> SkillAnimation;
    UPROPERTY() TObjectPtr<UBlendSpace1D> LocomotionBlendSpace;
    UPROPERTY() TObjectPtr<UStaticMeshComponent> WalkSurface;
    UPROPERTY() TObjectPtr<ACombatTrainingDummy> Target;
    UPROPERTY() TObjectPtr<UMaterialInstanceDynamic> AnimePost;
    UPROPERTY() TObjectPtr<UMaterialParameterCollection> StyleParameters;
    UPROPERTY() TObjectPtr<APostProcessVolume> PostVolume;
    float ForwardInput=0.f, RightInput=0.f;
    float Clock=0.f, NextAttack=0.f, NextSkill=0.f, ActionUntil=0.f;
    bool bMovingAnimation=false;
    bool bActionPlaying=false;
    bool bTestMode=false;
    bool bHasMoveDestination=false;
    bool bRightMouseHeld=false;
    bool bAnimeStyle=false;
    bool bShowcaseBattle=false;
    bool bStyleTest=false;
    bool bAlternateAttack=false;
    float StyleBlend=0.f;
    float LocomotionAlpha=0.f;
    FVector CurrentVelocity=FVector::ZeroVector;
    FVector MoveDestination=FVector::ZeroVector;
    float DesiredCameraDistance=760.f;
    void MoveForward(float Value);
    void MoveRight(float Value);
    void Zoom(float Value);
    void RightClickPressed();
    void RightClickReleased();
    void IssueMoveCommand();
    void SetMoveDestination(const FVector& WorldPoint);
    bool FindBattleGround(const FVector& WorldPoint, FVector& GroundPoint) const;
    void Attack();
    void Skill();
    void ResolveAttack();
    void ResolveSkill();
    void SelectAnimation(bool bMoving);
    void ResetTarget();
    void ToggleStyle();
    void ApplyStyle();
    void Quit();
};

UCLASS()
class ETERNALREBIRTH_API ACombatArenaHUD : public AHUD {
    GENERATED_BODY()
public:
    virtual void BeginPlay() override;
    virtual void DrawHUD() override;
private:
    UPROPERTY() TObjectPtr<UTexture2D> Portrait;
    UPROPERTY() TObjectPtr<UTexture2D> SealIcon;
    UPROPERTY() TObjectPtr<UTexture2D> CharmIcon;
    float DisplayedTargetHealth=600.f;
    void DrawPolishedHUD();
};

UCLASS()
class ETERNALREBIRTH_API ACombatArenaGameMode : public AGameModeBase {
    GENERATED_BODY()
public:
    ACombatArenaGameMode();
};
