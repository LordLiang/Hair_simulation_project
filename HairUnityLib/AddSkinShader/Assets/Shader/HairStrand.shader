﻿// Upgrade NOTE: replaced 'mul(UNITY_MATRIX_MVP,*)' with 'UnityObjectToClipPos(*)'

Shader "Custom/HairStrand" {
	Properties{
		_R("Hair Stroke Width", Float) = 0.00065
        _Color("Hair Color", Color) = (0.2431372553, 0.176470588, 0.160784314, 1.0)
        _KDiffuse("Diffuse Term", Range(0.0, 3.0)) = 0.98
        _KR("R Term", Range(0.0, 3.0)) = 1.1
        _KTT("TT Term", Range(0.0, 3.0)) = 0.65
        _KTRT("TRT Term", Range(0.0, 3.0)) = 1.45
	}
    
	SubShader {
		Tags {
			"RenderType"="Opaque"
			"Queue" = "Geometry"
		}
		Cull Off

        Pass {
            Tags {
                "LightMode"="ShadowCaster"
            }
            CGPROGRAM
            // Upgrade NOTE: excluded shader from OpenGL ES 2.0 because it uses non-square matrices
            #pragma exclude_renderers gles

            #pragma vertex vert
            #pragma fragment frag
            #pragma geometry geo
            #pragma multi_compile_shadowcaster
            #include "UnityCG.cginc"

            float _R;

            struct VS_INPUT {
                float4 vertex: POSITION;
                float3 adj_vertex: NORMAL;
            };

            struct GS_INPUT {
                float4 pos: POSITION;
                float4 adj_pos: NORMAL;
            };

            struct PS_INPUT {
                float4 pos: POSITION;
            };

            GS_INPUT vert(VS_INPUT v) {
                GS_INPUT g;

                //the equation in b-spine curve is no linear, we try to get the worldPosition in frag
                //shader, so we transfer to clip coordinate at last
                g.pos = mul(unity_ObjectToWorld, v.vertex);
                g.adj_pos = mul(unity_ObjectToWorld, v.adj_vertex);
                return g;
            }

            [maxvertexcount(62)]
            void geo(line GS_INPUT gs[2], inout TriangleStream<PS_INPUT> ps) {

                //get the stroke width in clip view by tranforming the (1.0f, 0.0f, 0.0f, 1.0f) in clip space back to object space
                float stroke_width = _R / length(mul(UNITY_MATRIX_IT_MV, mul(unity_CameraInvProjection, float4(1.0f, 0.0f, 0.0f, 1.0f))).xyz);

                float4 q0 = (-1 * gs[0].pos + 3 * gs[0].adj_pos - 3 * gs[1].pos + 1 * gs[1].adj_pos) / 6.0;
                float4 q1 = (3 * gs[0].pos - 6 * gs[0].adj_pos + 3 * gs[1].pos) / 6.0;
                float4 q2 = (-3 * gs[0].pos + 3 * gs[1].pos) / 6.0;
                float4 q3 = (1 * gs[0].pos + 4 * gs[0].adj_pos + 1 * gs[1].pos) / 6.0;

                PS_INPUT lst_v0, lst_v1, v0, v1;

                for (float u = 0.0f; u < 1.0001f; u += 0.10) {
                    float u2 = u * u;
                    float u3 = u2 * u;

                    float4 world_pos = u3 * q0 + u2 * q1 + u * q2 + q3; world_pos.w = 1.0f;
                    v0.pos = v1.pos = mul(UNITY_MATRIX_VP, world_pos);
                    v0.pos.x -= stroke_width;
                    v1.pos.x += stroke_width;

                    #ifndef SHADOWS_CUBE
                        v0.pos = UnityApplyLinearShadowBias(v0.pos);
                        v1.pos = UnityApplyLinearShadowBias(v1.pos);
                    #else
                        //TODO
                    #endif

                    if (u > 0) {
                        ps.Append(lst_v0);
                        ps.Append(lst_v1);
                        ps.Append(v0);
                        ps.RestartStrip();
                        ps.Append(lst_v1);
                        ps.Append(v0);
                        ps.Append(v1);
                        ps.RestartStrip();
                    }

                    lst_v0 = v0;
                    lst_v1 = v1;
                }
            }

            float4 frag(PS_INPUT p) : SV_TARGET{
                #ifndef SHADOWS_CUBE
                    return 0;
                #else
					return 0;
                #endif
            }

            ENDCG
        }


		Pass {
            Tags {
                "LightMode"="ForwardBase"
            }
			CGPROGRAM
            // Upgrade NOTE: excluded shader from OpenGL ES 2.0 because it uses non-square matrices
            #pragma exclude_renderers gles

			#pragma vertex vert
			#pragma fragment frag
			#pragma geometry geo
            #pragma multi_compile_fwdbase
			#include "UnityCG.cginc"
            #include "Lighting.cginc"
            #include "AutoLight.cginc"
			#include "Assets/Shader/HairFiberScattering.cginc"

			float _R;
            float3 _Color;
            float _KDiffuse;
            float _KR;
            float _KTT;
            float _KTRT;

			struct VS_INPUT {
				float4 vertex: POSITION;
				half4 color: COLOR;
				float3 adj_vertex: NORMAL;
			};

			struct GS_INPUT {
				float4 pos: POSITION;
				half4 color: COLOR0;
				float4 adj_pos: NORMAL;
			};

			struct PS_INPUT {
				float4 pos: POSITION;
                float4 world_tan: POSITION1;
                float4 world_pos: POSITION2;
				half4 color: COLOR0;
                SHADOW_COORDS(0)
			};

			GS_INPUT vert(VS_INPUT v) {
				GS_INPUT g;

                //the equation in b-spine curve is no linear, we try to get the worldPosition in frag
                //shader, so we transfer to clip coordinate at last
				g.pos = mul(unity_ObjectToWorld, v.vertex);//UnityObjectToClipPos(v.vertex);
				g.adj_pos = mul(unity_ObjectToWorld, v.adj_vertex);//UnityObjectToClipPos(v.adj_vertex);
				g.color = v.color;
				return g;
			}

			[maxvertexcount(30)]
			void geo(line GS_INPUT gs[2], inout TriangleStream<PS_INPUT> ps) {

                //get the stroke width in clip view by tranforming the (1.0f, 0.0f, 0.0f, 1.0f) in clip space back to object space
                float stroke_width = _R / length(mul(UNITY_MATRIX_IT_MV, mul(unity_CameraInvProjection, float4(1.0f, 0.0f, 0.0f, 1.0f))).xyz);

				float4 q0 = (-1 * gs[0].pos + 3 * gs[0].adj_pos - 3 * gs[1].pos + 1 * gs[1].adj_pos) / 6.0;
				float4 q1 = (3 * gs[0].pos - 6 * gs[0].adj_pos + 3 * gs[1].pos) / 6.0;
				float4 q2 = (-3 * gs[0].pos + 3 * gs[1].pos) / 6.0;
				float4 q3 = (1 * gs[0].pos + 4 * gs[0].adj_pos + 1 * gs[1].pos) / 6.0;

				PS_INPUT lst_v0, lst_v1, v0, v1;
                float4 lst_world_pos;

				for (float u = 0.0f; u < 1.0001f; u += 0.20) {
					float u2 = u * u;
					float u3 = u2 * u;

                    float4 world_pos = u3 * q0 + u2 * q1 + u * q2 + q3;
                    world_pos.w = 1.0f;

                    v0.pos = v1.pos = mul(UNITY_MATRIX_VP, world_pos);
                    v0.color = v1.color = gs[0].color * (1 - u) + gs[1].color * u;
                    v0.world_pos = v1.world_pos = world_pos;
                    TRANSFER_SHADOW(v0);
                    TRANSFER_SHADOW(v1);
					v0.pos.x -= stroke_width;
					v1.pos.x += stroke_width;

					if (u > 0) {
                        v0.world_tan = v1.world_tan = lst_v0.world_tan = lst_v1.world_tan = normalize(world_pos - lst_world_pos);
						ps.Append(lst_v0);
						ps.Append(lst_v1);
						ps.Append(v0);
						ps.RestartStrip();
						ps.Append(lst_v1);
						ps.Append(v0);
						ps.Append(v1);
						ps.RestartStrip();
					}

					lst_v0 = v0;
					lst_v1 = v1;
                    lst_world_pos = world_pos;
				}
			}

			half4 frag(PS_INPUT p) : SV_TARGET{

                UNITY_LIGHT_ATTENUATION(atten, p, (float3)p.world_pos);
                half3 light_color = atten * _LightColor0.rgb;
                //half3 mixed_color = light_color * p.color;

                #ifdef USING_DIRECTIONAL_LIGHT
                    float3 light_dir = normalize(_WorldSpaceLightPos0.xyz);
                #else
                    float3 light_dir = normalize(_WorldSpaceLightPos0.xyz - p.world_pos.xyz);
                #endif
                float3 normal = normalize(light_dir - dot(light_dir, p.world_tan) * p.world_tan);
                float3 view_dir = normalize(_WorldSpaceCameraPos.xyz - p.world_pos.xyz);
                float3 h = normalize(view_dir + light_dir);

                half3 ambient = UNITY_LIGHTMODEL_AMBIENT.xyz;

				return light_scattering_hair(p.color, light_color, ambient, light_dir, view_dir, p.world_tan, _KDiffuse, _KR, _KTT, _KTRT);
			}

			ENDCG
		}


		Pass {
			Tags {
				"LightMode"="ForwardAdd"
			}

			Blend One One

			CGPROGRAM
			// Upgrade NOTE: excluded shader from OpenGL ES 2.0 because it uses non-square matrices
			#pragma exclude_renderers gles

			#pragma vertex vert
			#pragma fragment frag
			#pragma geometry geo
			#pragma multi_compile_fwdadd
			#include "UnityCG.cginc"
			#include "Lighting.cginc"
			#include "AutoLight.cginc"
            #include "Assets/Shader/HairFiberScattering.cginc"

            float _R;
            float3 _Color;
            float _KDiffuse;
            float _KR;
            float _KTT;
            float _KTRT;

			struct VS_INPUT {
				float4 vertex: POSITION;
				half4 color: COLOR;
				float3 adj_vertex: NORMAL;
			};

			struct GS_INPUT {
				float4 pos: POSITION;
				half4 color: COLOR0;
				float4 adj_pos: NORMAL;
			};

			struct PS_INPUT {
				float4 pos: POSITION;
				float4 world_tan: POSITION1;
				float4 world_pos: POSITION2;
				half4 color: COLOR0;
				SHADOW_COORDS(0)
			};

			GS_INPUT vert(VS_INPUT v) {
				GS_INPUT g;

				//the equation in b-spine curve is no linear, we try to get the worldPosition in frag
				//shader, so we transfer to clip coordinate at last
				g.pos = mul(unity_ObjectToWorld, v.vertex);//UnityObjectToClipPos(v.vertex);
				g.adj_pos = mul(unity_ObjectToWorld, v.adj_vertex);//UnityObjectToClipPos(v.adj_vertex);
				g.color = v.color;
				return g;
			}

			[maxvertexcount(30)]
			void geo(line GS_INPUT gs[2], inout TriangleStream<PS_INPUT> ps) {

				//get the stroke width in clip view by tranforming the (1.0f, 0.0f, 0.0f, 1.0f) in clip space back to object space
				float stroke_width = _R / length(mul(UNITY_MATRIX_IT_MV, mul(unity_CameraInvProjection, float4(1.0f, 0.0f, 0.0f, 1.0f))).xyz);

				float4 q0 = (-1 * gs[0].pos + 3 * gs[0].adj_pos - 3 * gs[1].pos + 1 * gs[1].adj_pos) / 6.0;
				float4 q1 = (3 * gs[0].pos - 6 * gs[0].adj_pos + 3 * gs[1].pos) / 6.0;
				float4 q2 = (-3 * gs[0].pos + 3 * gs[1].pos) / 6.0;
				float4 q3 = (1 * gs[0].pos + 4 * gs[0].adj_pos + 1 * gs[1].pos) / 6.0;

				PS_INPUT lst_v0, lst_v1, v0, v1;
				float4 lst_world_pos;

				for (float u = 0.0f; u < 1.0001f; u += 0.20) {
					float u2 = u * u;
					float u3 = u2 * u;

					float4 world_pos = u3 * q0 + u2 * q1 + u * q2 + q3;
					world_pos.w = 1.0f;

					v0.pos = v1.pos = mul(UNITY_MATRIX_VP, world_pos);
					v0.color = v1.color = gs[0].color * (1 - u) + gs[1].color * u;
					v0.world_pos = v1.world_pos = world_pos;
					TRANSFER_SHADOW(v0);
					TRANSFER_SHADOW(v1);
					v0.pos.x -= stroke_width;
					v1.pos.x += stroke_width;

					if (u > 0) {
						v0.world_tan = v1.world_tan = lst_v0.world_tan = lst_v1.world_tan = normalize(world_pos - lst_world_pos);
						ps.Append(lst_v0);
						ps.Append(lst_v1);
						ps.Append(v0);
						ps.RestartStrip();
						ps.Append(lst_v1);
						ps.Append(v0);
						ps.Append(v1);
						ps.RestartStrip();
					}

					lst_v0 = v0;
					lst_v1 = v1;
					lst_world_pos = world_pos;
				}
			}

			half4 frag(PS_INPUT p) : SV_TARGET{

                UNITY_LIGHT_ATTENUATION(atten, p, (float3)p.world_pos);
                half3 light_color = atten * _LightColor0.rgb;
                //half3 mixed_color = light_color * p.color;

                #ifdef USING_DIRECTIONAL_LIGHT
                    float3 light_dir = normalize(_WorldSpaceLightPos0.xyz);
                #else
                    float3 light_dir = normalize(_WorldSpaceLightPos0.xyz - p.world_pos.xyz);
                #endif
                float3 normal = normalize(light_dir - dot(light_dir, p.world_tan) * p.world_tan);
                float3 view_dir = normalize(_WorldSpaceCameraPos.xyz - p.world_pos.xyz);
                float3 h = normalize(view_dir + light_dir);

                half3 ambient = UNITY_LIGHTMODEL_AMBIENT.xyz;

                return light_scattering_hair(p.color, light_color, ambient, light_dir, view_dir, p.world_tan, _KDiffuse, _KR, _KTT, _KTRT);
			}

			ENDCG
		}
	}
	FallBack "VertexLit"
}
