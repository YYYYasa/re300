#include "CombatPrototype.h"
#include "HeroSpellVisual.h"
#include "Animation/AnimSequence.h"
#include "Animation/BlendSpace1D.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "DrawDebugHelpers.h"
#include "Engine/Canvas.h"
#include "Engine/PostProcessVolume.h"
#include "Engine/DirectionalLight.h"
#include "Engine/SkyLight.h"
#include "Engine/ExponentialHeightFog.h"
#include "Components/DirectionalLightComponent.h"
#include "Components/SkyLightComponent.h"
#include "Components/ExponentialHeightFogComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialParameterCollection.h"
#include "Materials/MaterialInterface.h"
#include "Kismet/KismetMaterialLibrary.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/SpringArmComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/CommandLine.h"
#include "Misc/Paths.h"
#include "TimerManager.h"
#include "UnrealClient.h"

namespace {
template<class T> T* CombatAsset(const TCHAR* Path) { return LoadObject<T>(nullptr,Path); }
}

ACombatTrainingDummy::ACombatTrainingDummy() {
    PrimaryActorTick.bCanEverTick=false;
    Capsule=CreateDefaultSubobject<UCapsuleComponent>(TEXT("Capsule"));
    SetRootComponent(Capsule);
    Capsule->InitCapsuleSize(42.f,88.f);
    Capsule->SetCollisionProfileName(TEXT("Pawn"));
    Mesh=CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("HeroMesh"));
    Mesh->SetupAttachment(Capsule);
    Mesh->SetRelativeLocation(FVector(0,0,-80));
    Mesh->SetRelativeRotation(FRotator(180,360,-180));
    Mesh->SetRelativeScale3D(FVector(2));
    Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Mesh->SetSkeletalMesh(CombatAsset<USkeletalMesh>(TEXT("/Game/Art/Heroes/H013/SK_H013.SK_H013")));
}

void ACombatTrainingDummy::BeginPlay() {
    Super::BeginPlay();
    // The placed actor once had a 180-degree pitch, putting its head below ground.
    SetActorRotation(FRotator(0,-90,0));
    Health=MaxHealth;
    if(auto Idle=CombatAsset<UAnimSequence>(TEXT("/Game/Art/Heroes/H013/AN_H013_Idle.AN_H013_Idle"))) Mesh->PlayAnimation(Idle,true);
    UE_LOG(LogTemp,Display,TEXT("REBIRTH_COMBAT_DUMMY_READY health=%.0f"),Health);
}

bool ACombatTrainingDummy::ReceiveDamage(float Amount) {
    if(Health<=0) return false;
    Health=FMath::Max(0.f,Health-Amount);
    LastDamage=Amount;
    LastHitTime=GetWorld()->GetTimeSeconds();
    UE_LOG(LogTemp,Display,TEXT("REBIRTH_COMBAT_HIT damage=%.0f dummy_hp=%.0f"),Amount,Health);
    if(Health<=0) {
        Mesh->SetVisibility(false);
        GetWorldTimerManager().SetTimer(ResetTimer,this,&ACombatTrainingDummy::ResetDummy,3.f,false);
        UE_LOG(LogTemp,Display,TEXT("REBIRTH_COMBAT_DUMMY_DOWN"));
    }
    return true;
}

void ACombatTrainingDummy::ResetDummy() {
    Health=MaxHealth;
    Mesh->SetVisibility(true);
    UE_LOG(LogTemp,Display,TEXT("REBIRTH_COMBAT_DUMMY_RESET"));
}

ACombatHeroPawn::ACombatHeroPawn() {
    PrimaryActorTick.bCanEverTick=true;
    Capsule=CreateDefaultSubobject<UCapsuleComponent>(TEXT("Capsule"));
    SetRootComponent(Capsule);
    Capsule->InitCapsuleSize(42.f,88.f);
    Capsule->SetCollisionProfileName(TEXT("Pawn"));
    Mesh=CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("HeroMesh"));
    Mesh->SetupAttachment(Capsule);
    Mesh->SetRelativeLocation(FVector(0,0,-80));
    Mesh->SetRelativeRotation(FRotator(180,360,-180));
    Mesh->SetRelativeScale3D(FVector(2));
    Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Mesh->SetSkeletalMesh(CombatAsset<USkeletalMesh>(TEXT("/Game/Art/Heroes/H100/SK_H100.SK_H100")));
    CameraBoom=CreateDefaultSubobject<USpringArmComponent>(TEXT("CameraBoom"));
    CameraBoom->SetupAttachment(Capsule);
    CameraBoom->SetRelativeRotation(FRotator(-48,0,0));
    CameraBoom->TargetArmLength=760.f;
    CameraBoom->bDoCollisionTest=false;
    CameraBoom->bUsePawnControlRotation=false;
    CameraBoom->SetUsingAbsoluteRotation(true);
    Camera=CreateDefaultSubobject<UCameraComponent>(TEXT("Camera"));
    Camera->SetupAttachment(CameraBoom,USpringArmComponent::SocketName);
    Camera->FieldOfView=62.f;
    AutoPossessPlayer=EAutoReceiveInput::Player0;
}

void ACombatHeroPawn::BeginPlay() {
    Super::BeginPlay();
    bShowcaseBattle=GetWorld()->GetMapName().Contains(TEXT("EternalCombat"));
    bAnimeStyle=FParse::Param(FCommandLine::Get(),TEXT("Anime"));
    bStyleTest=FParse::Param(FCommandLine::Get(),TEXT("RebirthCombatStyleTest"));
    for(TActorIterator<APostProcessVolume> It(GetWorld());It;++It) {
        if(It->bUnbound) { PostVolume=*It; break; }
    }
    StyleParameters=CombatAsset<UMaterialParameterCollection>(TEXT("/Game/Art/Materials/MPC_Style.MPC_Style"));
    if(auto Mat=CombatAsset<UMaterialInterface>(TEXT("/Game/Art/Materials/M_AnimePost.M_AnimePost"))) {
        AnimePost=UMaterialInstanceDynamic::Create(Mat,this);
        Camera->PostProcessSettings.AddBlendable(AnimePost,1.f);
        Camera->PostProcessBlendWeight=1.f;
    }
    StyleBlend=bAnimeStyle?1.f:0.f;
    if(AnimePost) AnimePost->SetScalarParameterValue(TEXT("AnimeMix"),StyleBlend);
    if(StyleParameters) UKismetMaterialLibrary::SetScalarParameterValue(this,StyleParameters,TEXT("AnimeMix"),StyleBlend);
    ApplyStyle();
    IdleAnimation=CombatAsset<UAnimSequence>(TEXT("/Game/Art/Heroes/H100/AN_H100_Idle.AN_H100_Idle"));
    RunAnimation=CombatAsset<UAnimSequence>(TEXT("/Game/Art/Heroes/H100/AN_H100_Run.AN_H100_Run"));
    AttackAnimation=CombatAsset<UAnimSequence>(TEXT("/Game/Art/Heroes/H100/AN_H100_Attack.AN_H100_Attack"));
    AttackAnimation2=CombatAsset<UAnimSequence>(TEXT("/Game/Art/Heroes/H100/AN_H100_single_attack_attcom_2.AN_H100_single_attack_attcom_2"));
    SkillAnimation=CombatAsset<UAnimSequence>(TEXT("/Game/Art/Heroes/H100/AN_H100_single_skill_02.AN_H100_single_skill_02"));
    LocomotionBlendSpace=CombatAsset<UBlendSpace1D>(TEXT("/Game/Art/Heroes/H100/BS_H100_Locomotion.BS_H100_Locomotion"));
    Target=Cast<ACombatTrainingDummy>(UGameplayStatics::GetActorOfClass(GetWorld(),ACombatTrainingDummy::StaticClass()));
    if(LocomotionBlendSpace) Mesh->PlayAnimation(LocomotionBlendSpace,true);
    else if(IdleAnimation) Mesh->PlayAnimation(IdleAnimation,true);
    if(bShowcaseBattle) {
        // The dedicated walk mesh determines traversable terrain and elevation.
        // Beauty meshes contain oversized import hulls and must not block the pawn.
        Capsule->SetCollisionResponseToChannel(ECC_WorldStatic,ECR_Ignore);
        for(TActorIterator<AActor> It(GetWorld());It;++It)
            if(It->ActorHasTag(TEXT("BattleWalkSurface"))) {
                WalkSurface=It->FindComponentByClass<UStaticMeshComponent>();
                Capsule->IgnoreActorWhenMoving(*It,true);
            }
        DesiredCameraDistance=1050.f;
        CameraBoom->TargetArmLength=DesiredCameraDistance;
        FVector Ground=FVector::ZeroVector;
        const bool bGroundFound=FindBattleGround(GetActorLocation(),Ground);
        UE_LOG(LogTemp,Display,TEXT("REBIRTH_BATTLE_GROUND_START found=%d at=%s"),
            bGroundFound,*Ground.ToCompactString());
        if(bGroundFound)
            SetActorLocation(FVector(GetActorLocation().X,GetActorLocation().Y,Ground.Z+88.f));
    }
    SetActorRotation(FRotator(0,90,0));
    if(auto PC=Cast<APlayerController>(Controller)) {
        PC->bShowMouseCursor=true;
        FInputModeGameAndUI Mode;
        Mode.SetHideCursorDuringCapture(false);
        Mode.SetLockMouseToViewportBehavior(EMouseLockMode::LockAlways);
        PC->SetInputMode(Mode);
    }
    UE_LOG(LogTemp,Display,TEXT("REBIRTH_COMBAT_READY hero=H100 idle=%d run=%d attack=%d blend=%d skill=%d dummy=%d"),
        IdleAnimation!=nullptr,RunAnimation!=nullptr,AttackAnimation!=nullptr,
        LocomotionBlendSpace!=nullptr,SkillAnimation!=nullptr,Target!=nullptr);
    UE_LOG(LogTemp,Display,TEXT("REBIRTH_COMBAT_MAP map=%s style=%s post=%d collection=%d"),
        *GetWorld()->GetMapName(),bAnimeStyle?TEXT("anime"):TEXT("realistic"),AnimePost!=nullptr,StyleParameters!=nullptr);
    if(bStyleTest) {
        FTimerHandle RealisticShot;
        GetWorldTimerManager().SetTimer(RealisticShot,[]() {
            FScreenshotRequest::RequestScreenshot(FPaths::ProjectSavedDir()/TEXT("Screenshots/EternalCombat_Realistic.png"),false,false);
        },7.f,false);
        FTimerHandle SwitchTimer;
        GetWorldTimerManager().SetTimer(SwitchTimer,this,&ACombatHeroPawn::ToggleStyle,8.f,false);
        FTimerHandle AnimeShot;
        GetWorldTimerManager().SetTimer(AnimeShot,[]() {
            FScreenshotRequest::RequestScreenshot(FPaths::ProjectSavedDir()/TEXT("Screenshots/EternalCombat_Anime.png"),false,false);
        },10.f,false);
        FTimerHandle QuitTimer;
        GetWorldTimerManager().SetTimer(QuitTimer,this,&ACombatHeroPawn::Quit,11.f,false);
    }
    bTestMode=FParse::Param(FCommandLine::Get(),TEXT("RebirthCombatTest"));
    if(FParse::Param(FCommandLine::Get(),TEXT("RebirthUpgradeTest"))) {
        auto Later=[this](float Time, TFunction<void()> Fn) {
            FTimerHandle Handle;
            GetWorldTimerManager().SetTimer(Handle,FTimerDelegate::CreateLambda(MoveTemp(Fn)),Time,false);
        };
        Later(2.f,[this]() {
            TArray<FBlendSampleData> Samples;
            int32 Index=INDEX_NONE;
            const bool Valid=LocomotionBlendSpace && LocomotionBlendSpace->GetSamplesFromBlendInput(FVector(.5,0,0),Samples,Index,true);
            UE_LOG(LogTemp,Display,TEXT("REBIRTH_UPGRADE_BLEND valid=%d samples=%d"),Valid,Samples.Num());
            Zoom(-100); Zoom(100); Zoom(-4.27778f);
            SetMoveDestination(FVector(2400,-1800,0));
        });
        Later(7.f,[this]() {
            UE_LOG(LogTemp,Display,TEXT("REBIRTH_UPGRADE_TRAVERSE location=%s alpha=%.3f beyond_old_bounds=%d"),
                *GetActorLocation().ToCompactString(),LocomotionAlpha,GetActorLocation().X>1800.f);
            SetMoveDestination(GetActorLocation()+FVector(1000,0,0));
        });
        Later(8.f,[this]() { bHasMoveDestination=false; UE_LOG(LogTemp,Display,TEXT("REBIRTH_UPGRADE_STOP initial=%.3f"),LocomotionAlpha); });
        Later(8.15f,[this]() { UE_LOG(LogTemp,Display,TEXT("REBIRTH_UPGRADE_STOP middle=%.3f"),LocomotionAlpha); });
        Later(9.f,[this]() { UE_LOG(LogTemp,Display,TEXT("REBIRTH_UPGRADE_STOP settled=%.3f"),LocomotionAlpha); });
        Later(10.f,[this]() { if(Target) { SetActorLocation(Target->GetActorLocation()-FVector(150,0,0)); CurrentVelocity=FVector::ZeroVector; Attack(); } });
        Later(10.35f,[]() { FScreenshotRequest::RequestScreenshot(FPaths::ProjectSavedDir()/TEXT("Screenshots/Upgrade_Attack.png"),false,false); });
        Later(12.f,[this]() { Skill(); });
        Later(12.65f,[]() { FScreenshotRequest::RequestScreenshot(FPaths::ProjectSavedDir()/TEXT("Screenshots/Upgrade_Skill.png"),false,false); });
        Later(14.f,[this]() { ToggleStyle(); });
        Later(16.f,[]() { FScreenshotRequest::RequestScreenshot(FPaths::ProjectSavedDir()/TEXT("Screenshots/Upgrade_Anime.png"),false,false); });
        Later(17.f,[this]() { Quit(); });
    }
    if(bTestMode && Target) {
        SetActorLocation(Target->GetActorLocation()-FVector(350,0,0));
        SetMoveDestination(Target->GetActorLocation()-FVector(100,0,0));
        FTimerHandle RunShotTimer;
        GetWorldTimerManager().SetTimer(RunShotTimer,[]() {
            FScreenshotRequest::RequestScreenshot(FPaths::ProjectSavedDir()/TEXT("Screenshots/Combat_Run.png"),false,false);
        },.35f,false);
        FTimerHandle AttackTimer;
        GetWorldTimerManager().SetTimer(AttackTimer,this,&ACombatHeroPawn::Attack,.7f,false);
        FTimerHandle AttackShotTimer;
        GetWorldTimerManager().SetTimer(AttackShotTimer,[]() {
            FScreenshotRequest::RequestScreenshot(FPaths::ProjectSavedDir()/TEXT("Screenshots/Combat_Attack.png"),false,false);
        },.9f,false);
        FTimerHandle SkillTimer;
        GetWorldTimerManager().SetTimer(SkillTimer,this,&ACombatHeroPawn::Skill,1.7f,false);
        FTimerHandle ScreenshotTimer;
        GetWorldTimerManager().SetTimer(ScreenshotTimer,[this]() {
            FScreenshotRequest::RequestScreenshot(FPaths::ProjectSavedDir()/TEXT("Screenshots/CombatPrototype.png"),false,false);
            UE_LOG(LogTemp,Display,TEXT("REBIRTH_COMBAT_SCREENSHOT"));
        },2.8f,false);
        for(int32 Index=0;Index<5;Index++) {
            FTimerHandle RepeatTimer;
            GetWorldTimerManager().SetTimer(RepeatTimer,this,&ACombatHeroPawn::Attack,3.2f+Index*.8f,false);
        }
        FTimerHandle ResetShotTimer;
        GetWorldTimerManager().SetTimer(ResetShotTimer,[]() {
            FScreenshotRequest::RequestScreenshot(FPaths::ProjectSavedDir()/TEXT("Screenshots/Combat_Reset.png"),false,false);
        },9.9f,false);
        FTimerHandle ZoomTimer;
        GetWorldTimerManager().SetTimer(ZoomTimer,[this]() { Zoom(2.f); },8.7f,false);
        FTimerHandle QuitTimer;
        GetWorldTimerManager().SetTimer(QuitTimer,[this]() { GetWorld()->GetFirstPlayerController()->ConsoleCommand(TEXT("quit")); },10.6f,false);
    }
}

float ACombatHeroPawn::AttackCooldownRemaining() const { return FMath::Max(0.f,NextAttack-Clock); }
float ACombatHeroPawn::SkillCooldownRemaining() const { return FMath::Max(0.f,NextSkill-Clock); }
void ACombatHeroPawn::MoveForward(float Value) { ForwardInput=Value; }
void ACombatHeroPawn::MoveRight(float Value) { RightInput=Value; }
void ACombatHeroPawn::Zoom(float Value) {
    if(FMath::IsNearlyZero(Value)) return;
    DesiredCameraDistance=FMath::Clamp(DesiredCameraDistance-Value*180.f,280.f,4500.f);
    UE_LOG(LogTemp,Display,TEXT("REBIRTH_COMBAT_ZOOM target=%.0f"),DesiredCameraDistance);
}

void ACombatHeroPawn::SetMoveDestination(const FVector& WorldPoint) {
    FVector NewDestination;
    if(bShowcaseBattle) {
        FVector Ground;
        if(!FindBattleGround(WorldPoint,Ground)) {
            UE_LOG(LogTemp,Display,TEXT("REBIRTH_COMBAT_MOVE_REJECT no_walk_surface x=%.0f y=%.0f"),WorldPoint.X,WorldPoint.Y);
            return;
        }
        NewDestination=Ground+FVector(0,0,88.f);
    } else {
        NewDestination=FVector(FMath::Clamp(WorldPoint.X,-770.f,770.f),
                               FMath::Clamp(WorldPoint.Y,-770.f,770.f),GetActorLocation().Z);
    }
    if(bHasMoveDestination && FVector::Dist2D(NewDestination,MoveDestination)<12.f) return;
    MoveDestination=NewDestination;
    bHasMoveDestination=true;
    UE_LOG(LogTemp,Display,TEXT("REBIRTH_COMBAT_MOVE_COMMAND x=%.0f y=%.0f z=%.0f"),
        MoveDestination.X,MoveDestination.Y,MoveDestination.Z);
}

bool ACombatHeroPawn::FindBattleGround(const FVector& WorldPoint, FVector& GroundPoint) const {
    FHitResult Hit;
    FCollisionQueryParams Params(SCENE_QUERY_STAT(BattleGround),true);
    Params.AddIgnoredActor(this);
    if(Target) Params.AddIgnoredActor(Target);
    const FVector Start(WorldPoint.X,WorldPoint.Y,5000.f);
    const FVector End(WorldPoint.X,WorldPoint.Y,-5000.f);
    if(WalkSurface && WalkSurface->LineTraceComponent(Hit,Start,End,Params)) {
        GroundPoint=Hit.ImpactPoint;
        return true;
    }
    return false;
}

void ACombatHeroPawn::IssueMoveCommand() {
    auto PC=Cast<APlayerController>(Controller);
    if(!PC) return;
    FVector RayOrigin,RayDirection;
    if(!PC->DeprojectMousePositionToWorld(RayOrigin,RayDirection) || RayDirection.Z>=-.001f) return;
    if(bShowcaseBattle) {
        FHitResult Hit;
        FCollisionQueryParams Params(SCENE_QUERY_STAT(BattleMouse),true);
        Params.AddIgnoredActor(this);
        if(Target) Params.AddIgnoredActor(Target);
        if(WalkSurface && WalkSurface->LineTraceComponent(Hit,RayOrigin,RayOrigin+RayDirection*100000.f,Params))
            SetMoveDestination(Hit.ImpactPoint);
    } else {
        const float Distance=-RayOrigin.Z/RayDirection.Z;
        if(Distance>0) SetMoveDestination(RayOrigin+RayDirection*Distance);
    }
}

void ACombatHeroPawn::RightClickPressed() { bRightMouseHeld=true; IssueMoveCommand(); }
void ACombatHeroPawn::RightClickReleased() { bRightMouseHeld=false; }

void ACombatHeroPawn::Tick(float DeltaTime) {
    Super::Tick(DeltaTime);
    Clock+=DeltaTime;
    StyleBlend=FMath::FInterpTo(StyleBlend,bAnimeStyle?1.f:0.f,DeltaTime,4.f);
    if(AnimePost) AnimePost->SetScalarParameterValue(TEXT("AnimeMix"),StyleBlend);
    if(StyleParameters) UKismetMaterialLibrary::SetScalarParameterValue(this,StyleParameters,TEXT("AnimeMix"),StyleBlend);
    CameraBoom->TargetArmLength=FMath::FInterpTo(CameraBoom->TargetArmLength,DesiredCameraDistance,DeltaTime,9.f);
    if(bRightMouseHeld) IssueMoveCommand();
    FVector Direction(ForwardInput,RightInput,0);
    if(!Direction.IsNearlyZero()) bHasMoveDestination=false;
    else if(bHasMoveDestination) {
        const FVector ToGoal=MoveDestination-GetActorLocation();
        if(ToGoal.Size2D()<=12.f) bHasMoveDestination=false;
        else Direction=ToGoal.GetSafeNormal2D()*FMath::Clamp(ToGoal.Size2D()/100.f,0.f,1.f);
    }
    Direction=Direction.GetClampedToMaxSize(1.f);
    const bool bMoving=!Direction.IsNearlyZero();
    CurrentVelocity=FMath::VInterpTo(CurrentVelocity,Direction*420.f,DeltaTime,bMoving?10.f:7.f);
    if(CurrentVelocity.Size2D()<2.f) CurrentVelocity=FVector::ZeroVector;
    LocomotionAlpha=FMath::FInterpTo(LocomotionAlpha,CurrentVelocity.Size2D()/420.f,DeltaTime,7.f);
    if(!CurrentVelocity.IsNearlyZero()) {
        FHitResult Hit;
        FVector Next=GetActorLocation()+CurrentVelocity*DeltaTime;
        if(bShowcaseBattle) {
            FVector Ground;
            if(!FindBattleGround(Next,Ground)) {
                CurrentVelocity=FVector::ZeroVector;
                bHasMoveDestination=false;
                UE_LOG(LogTemp,Display,TEXT("REBIRTH_COMBAT_EDGE_STOP x=%.0f y=%.0f"),Next.X,Next.Y);
                Next=GetActorLocation();
            } else Next.Z=Ground.Z+88.f;
        }
        AddActorWorldOffset(Next-GetActorLocation(),true,&Hit);
        if(Hit.IsValidBlockingHit() && bHasMoveDestination) bHasMoveDestination=false;
        if(Clock>=ActionUntil && CurrentVelocity.Size2D()>15.f) {
            const FRotator Facing=CurrentVelocity.Rotation()+FRotator(0,90,0);
            SetActorRotation(FMath::RInterpTo(GetActorRotation(),Facing,DeltaTime,12.f));
        }
    }
    if(Clock>=ActionUntil) {
        if(bActionPlaying) {
            bActionPlaying=false;
            if(LocomotionBlendSpace) Mesh->PlayAnimation(LocomotionBlendSpace,true);
            else bMovingAnimation=!bMoving;
        }
        SelectAnimation(LocomotionAlpha>.08f);
        if(LocomotionBlendSpace)
            if(auto Instance=Cast<UAnimSingleNodeInstance>(Mesh->GetAnimInstance()))
                Instance->SetBlendSpacePosition(FVector(LocomotionAlpha,0,0));
    }
}

void ACombatHeroPawn::SelectAnimation(bool bMoving) {
    if(bMoving==bMovingAnimation) return;
    bMovingAnimation=bMoving;
    if(LocomotionBlendSpace) {
        UE_LOG(LogTemp,Display,TEXT("REBIRTH_COMBAT_ANIM_BLEND %s alpha=%.2f"),
            bMoving?TEXT("Run"):TEXT("Idle"),LocomotionAlpha);
    } else if(auto Sequence=bMoving?RunAnimation.Get():IdleAnimation.Get()) {
        Mesh->PlayAnimation(Sequence,true);
        UE_LOG(LogTemp,Display,TEXT("REBIRTH_COMBAT_ANIM %s"),bMoving?TEXT("Run"):TEXT("Idle"));
    }
}

void ACombatHeroPawn::Attack() {
    if(Clock<NextAttack || Clock<ActionUntil) return;
    NextAttack=Clock+.75f;
    ActionUntil=Clock+.70f;
    bActionPlaying=true;
    if(Target) SetActorRotation((Target->GetActorLocation()-GetActorLocation()).Rotation()+FRotator(0,90,0));
    UAnimSequence* Selected=bAlternateAttack && AttackAnimation2?AttackAnimation2.Get():AttackAnimation.Get();
    bAlternateAttack=!bAlternateAttack;
    if(Selected) {
        Mesh->PlayAnimation(Selected,false);
        if(auto Instance=Cast<UAnimSingleNodeInstance>(Mesh->GetAnimInstance())) Instance->SetPlayRate(2.f);
    }
    FTimerHandle HitTimer;
    GetWorldTimerManager().SetTimer(HitTimer,this,&ACombatHeroPawn::ResolveAttack,.24f,false);
    UE_LOG(LogTemp,Display,TEXT("REBIRTH_COMBAT_ATTACK_START"));
}

void ACombatHeroPawn::ResolveAttack() {
    if(!Target || Target->Health<=0) return;
    const float Distance=FVector::Dist2D(GetActorLocation(),Target->GetActorLocation());
    if(Distance>245.f) { UE_LOG(LogTemp,Display,TEXT("REBIRTH_COMBAT_ATTACK_MISS distance=%.0f"),Distance); return; }
    if(auto FX=GetWorld()->SpawnActor<AHeroSpellVisual>(Target->GetActorLocation()+FVector(0,0,45),FRotator::ZeroRotator)) FX->Initialize(false);
    Target->ReceiveDamage(75.f);
}

void ACombatHeroPawn::Skill() {
    if(Clock<NextSkill || Clock<ActionUntil) return;
    NextSkill=Clock+6.f;
    ActionUntil=Clock+.65f;
    bActionPlaying=true;
    if(Target) SetActorRotation((Target->GetActorLocation()-GetActorLocation()).Rotation()+FRotator(0,90,0));
    if(auto Selected=SkillAnimation?SkillAnimation.Get():AttackAnimation.Get()) Mesh->PlayAnimation(Selected,false);
    FTimerHandle HitTimer;
    GetWorldTimerManager().SetTimer(HitTimer,this,&ACombatHeroPawn::ResolveSkill,.34f,false);
    UE_LOG(LogTemp,Display,TEXT("REBIRTH_COMBAT_SKILL_START"));
}

void ACombatHeroPawn::ResolveSkill() {
    const FVector Center=GetActorLocation()-GetActorRightVector()*190.f;
    if(auto FX=GetWorld()->SpawnActor<AHeroSpellVisual>(Center-FVector(0,0,80),FRotator::ZeroRotator)) FX->Initialize(true);
    if(Target && Target->Health>0 && FVector::Dist2D(Center,Target->GetActorLocation())<=180.f)
        Target->ReceiveDamage(165.f);
    else UE_LOG(LogTemp,Display,TEXT("REBIRTH_COMBAT_SKILL_MISS"));
}

void ACombatHeroPawn::ResetTarget() { if(Target) Target->ResetDummy(); }
void ACombatHeroPawn::Quit() { if(auto PC=Cast<APlayerController>(Controller)) PC->ConsoleCommand(TEXT("quit")); }

void ACombatHeroPawn::ToggleStyle() {
    bAnimeStyle=!bAnimeStyle;
    ApplyStyle();
    UE_LOG(LogTemp,Display,TEXT("REBIRTH_COMBAT_STYLE %s"),bAnimeStyle?TEXT("anime"):TEXT("realistic"));
}

void ACombatHeroPawn::ApplyStyle() {
    for(TActorIterator<ADirectionalLight> It(GetWorld());It;++It) {
        auto Light=Cast<UDirectionalLightComponent>(It->GetLightComponent());
        Light->SetIntensity(bAnimeStyle?4.2f:4.7f);
        Light->SetLightColor(bAnimeStyle?FLinearColor(1,.94f,.87f):FLinearColor(1,.92f,.80f));
        Light->SetLightSourceAngle(bAnimeStyle?3.f:8.f);
        Light->SetShadowAmount(bAnimeStyle?.82f:.58f);
        It->SetActorRotation(bAnimeStyle?FRotator(-48,-35,0):FRotator(-49,-32,0));
    }
    for(TActorIterator<ASkyLight> It(GetWorld());It;++It) {
        It->GetLightComponent()->SetIntensity(bAnimeStyle?1.3f:2.f);
        It->GetLightComponent()->SetLightColor(bAnimeStyle?FLinearColor(.68f,.83f,1):FLinearColor(.85f,.91f,1));
    }
    for(TActorIterator<AExponentialHeightFog> It(GetWorld());It;++It) {
        It->GetComponent()->SetFogDensity(bAnimeStyle?.0035f:.006f);
        It->GetComponent()->SetFogInscatteringColor(bAnimeStyle?FLinearColor(.40f,.66f,.88f):FLinearColor(.45f,.54f,.60f));
    }
    if(PostVolume) {
        auto& S=PostVolume->Settings;
        S.bOverride_BloomIntensity=true; S.BloomIntensity=bAnimeStyle?.20f:.32f;
        S.bOverride_VignetteIntensity=true; S.VignetteIntensity=bAnimeStyle?.10f:.13f;
        S.bOverride_ColorSaturation=true; S.ColorSaturation=FVector4(1.f,1.f,1.f,bAnimeStyle?1.14f:1.f);
        S.bOverride_ColorContrast=true; S.ColorContrast=FVector4(1.f,1.f,1.f,bAnimeStyle?1.02f:1.01f);
        S.bOverride_AmbientOcclusionIntensity=true; S.AmbientOcclusionIntensity=bAnimeStyle?.35f:.20f;
    }
}

void ACombatHeroPawn::SetupPlayerInputComponent(UInputComponent* Input) {
    Super::SetupPlayerInputComponent(Input);
    Input->BindAxis(TEXT("Forward"),this,&ACombatHeroPawn::MoveForward);
    Input->BindAxis(TEXT("Right"),this,&ACombatHeroPawn::MoveRight);
    Input->BindAxis(TEXT("CombatZoom"),this,&ACombatHeroPawn::Zoom);
    Input->BindAction(TEXT("BattleMove"),IE_Pressed,this,&ACombatHeroPawn::RightClickPressed);
    Input->BindAction(TEXT("BattleMove"),IE_Released,this,&ACombatHeroPawn::RightClickReleased);
    Input->BindAction(TEXT("BattleAttack"),IE_Pressed,this,&ACombatHeroPawn::Attack);
    Input->BindAction(TEXT("BattleSkill"),IE_Pressed,this,&ACombatHeroPawn::Skill);
    Input->BindAction(TEXT("BattleReset"),IE_Pressed,this,&ACombatHeroPawn::ResetTarget);
    Input->BindAction(TEXT("Style"),IE_Pressed,this,&ACombatHeroPawn::ToggleStyle);
    Input->BindAction(TEXT("Quit"),IE_Pressed,this,&ACombatHeroPawn::Quit);
}

void ACombatArenaHUD::DrawHUD() {
    Super::DrawHUD();
    DrawPolishedHUD();
}

ACombatArenaGameMode::ACombatArenaGameMode() {
    DefaultPawnClass=ACombatHeroPawn::StaticClass();
    HUDClass=ACombatArenaHUD::StaticClass();
}
