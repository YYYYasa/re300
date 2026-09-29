"""Keep distant hills softly lit so nearby ruins do not cast giant silhouettes on them."""
import unreal as u
el=u.EditorAssetLibrary;ml=u.MaterialEditingLibrary
m=u.load_asset('/Game/Art/Atmosphere/M_DistantHighlands')
ml.delete_all_material_expressions(m)
m.set_editor_property('shading_model',u.MaterialShadingModel.MSM_UNLIT)
m.set_editor_property('two_sided',True)
p=ml.create_material_expression(m,u.MaterialExpressionWorldPosition,-400,0)
n=ml.create_material_expression(m,u.MaterialExpressionVertexNormalWS,-400,200)
inputs=[]
for name,node in [('P',p),('N',n)]:
    x=u.CustomInput();x.set_editor_property('input_name',name);inputs.append(x)
shader='float f=sin(P.x*.0015+sin(P.y*.0005))*sin(P.y*.0018)*.5+.5;float stone=1-smoothstep(.48,.90,N.z);float h=saturate((P.z+2500)/8500);float3 pine=lerp(float3(.035,.073,.069),float3(.095,.135,.110),f);float3 slate=lerp(float3(.16,.18,.17),float3(.26,.29,.28),f);return lerp(pine,slate,saturate(stone*.6+h*.20));'
c=ml.create_material_expression(m,u.MaterialExpressionCustom,0,0);c.set_editor_property('code',shader);c.set_editor_property('output_type',u.CustomMaterialOutputType.CMOT_FLOAT3);c.set_editor_property('inputs',inputs)
ml.connect_material_expressions(p,'',c,'P');ml.connect_material_expressions(n,'',c,'N')
ml.connect_material_property(c,'',u.MaterialProperty.MP_EMISSIVE_COLOR)
ml.layout_material_expressions(m);ml.recompile_material(m)
if not el.save_loaded_asset(m,False):raise RuntimeError('Distant material save failed')
u.log('REBIRTH: DISTANT_LIGHTING_COMPLETE')
