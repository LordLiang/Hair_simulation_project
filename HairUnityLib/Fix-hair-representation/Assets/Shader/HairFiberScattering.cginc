//Based on "Light Scattering from Human Hair Fibers"
// Upgrade NOTE: excluded shader from DX11, OpenGL ES 2.0 because it uses unsized arrays
#pragma exclude_renderers d3d11 gles

inline float pow2(float x)
{
    return x * x;
}

inline float fresnel(float eta, float cos_i) {
    float sin_i = sqrt(1 - cos_i * cos_i);
    float sin_t = sin_i / eta;
    float cos_t = sqrt(1 - sin_t * sin_t);
    float rs = pow2((cos_i - eta * cos_t) / (cos_i + eta * cos_t));
    float rt = pow2((cos_t - eta * cos_i) / (cos_t + eta * cos_i));
    return 0.5f * (rs + rt);
}

inline float g(float b, float x) {
    return 0.3989422804014327f / b * exp(-pow2(x / b) * 0.5f);
}

inline float I0(float x) 
{
    float factor[] = {
        1.0,
        0.25,
        0.015625,
        0.00043402777777777775,
        6.781684027777777e-06,
        6.781684027777778e-08,
        4.709502797067901e-10,
        2.4028075495244395e-12,
        9.385966990329842e-15,
        2.896903392077112e-17,
        7.242258480192778e-20 
    }; 

    float p = 1.0f;
    float ret = 0.0f;
    for (int i = 0; i <= 10; ++i) {
        ret += factor[i] * p;
        p *= (x * x);
    }

    return ret;
}

inline float csch(float x) 
{
    return 2.0 / (exp(x) - exp(-x));
}

inline float Mp(float b, float theta_i, float theta_o) 
{
    //float a = csch(1 / v) / (2 * v);
    //float b = exp(sin(-theta_i) * sin(theta_o) / v);
    //float c = I0(cos(-theta_i) * cos(theta_o) / v);
    //return a * b * c;
    return g(b, theta_o + theta_i);
}

inline half4 light_scattering_hair(float3 base_color, float3 light_color, float3 ambient_color, float3 i, float3 o, float3 u, float kd, float kr, float ktt, float ktrt)
{
    const float PI = 3.141592653589793f;
    const float PI2 = 2 * PI;
    const float ETA = 1.55f;
    const float DEGREE = PI / 180.0f;
    const float ALPHA_R = -8 * DEGREE;
    const float ALPHA_TT = -ALPHA_R * 0.5f;
    const float ALPHA_TRT = -ALPHA_R * 1.5f;

    const float BETA_R = 8.102 * DEGREE;
    const float BETA_TT = BETA_R * 0.5f;
    const float BETA_TRT = BETA_R * 2.0f;

    const float NP_CALC_STEP = 0.05f;

    float3 s = float3(0.0f, 0.0f, 0.0f);

    float3 i_proj = normalize(i - dot(i, u) * u);
    float3 o_proj = normalize(o - dot(o, u) * u);
    float cos_theta_i = dot(i, i_proj);
    float cos_theta_o = dot(o, o_proj);
    float sin_theta_i = sqrt(1 - pow2(cos_theta_i)) * sign(dot(i,u));
    float sin_theta_o = sqrt(1 - pow2(cos_theta_o)) * sign(dot(o,u));
    float theta_i = asin(sin_theta_i);
    float theta_o = asin(sin_theta_o);

    float theta_d = 0.5 * (theta_o - theta_i);
    float cos_theta_d = cos(theta_d);
    float sin_theta_d = sin(theta_d);

    float phi = acos(dot(i_proj, o_proj));
    float cos_phi = cos(phi);
    float sin_phi = sin(phi);
    float cos_half_phi = cos(phi / 2.0f);
    float sin_half_phi = sin(phi / 2.0f);

    float cos_io = dot(i, o);
    float cos_half_io = sqrt(0.5f + 0.5 * cos_io);

    float ETA_PRIME = sqrt(ETA * ETA - pow2(sin_theta_d)) / cos_theta_d;

    //diffuse term
    s += kd * light_color * base_color * max(0.0f, 0.75 * cos_theta_i * cos_half_phi + 0.25f);

    //R term
    float mr = Mp(BETA_R, theta_i, theta_o - ALPHA_R);
    float nr = fresnel(ETA, sqrt(dot(i, o) * 0.5f + 0.5f)) * 0.25 * cos_half_phi;
    s += kr * light_color * mr * nr;

    //TT term
    float mtt = Mp(BETA_TT, theta_i, theta_o - ALPHA_TT);
    float a = 1 / ETA_PRIME;
    float h = cos_half_phi * rsqrt(1 + a * a - 2 * a * sin_half_phi);
    //float3 ttt = light_color * exp(-2 * miu_prime * (2 - pow2(h) / pow2(ETA_PRIME)));
    float3 ttt = pow(light_color * base_color, 0.5 * sqrt(1 - pow2(h) / pow2(ETA_PRIME)) / cos_theta_d);
    float f = fresnel(ETA, cos_theta_d * sqrt(saturate(1 - h * h)));
    float ftt = pow2(1 - f);
    float stt = 0.3f;
    phi = 120 * DEGREE;
    float ntt = exp((phi - PI) / stt) / (stt * pow2(1 + exp((phi - PI) / stt)));
    s += ktt * ttt * mtt * ftt * ntt;

    //TRT term
    float mtrt = Mp(BETA_TRT, theta_i, theta_o - ALPHA_TRT);
    f = fresnel(ETA, cos_theta_d * 0.5);
    float ftrt = pow2(1 - f) * f;
    float3 ttrt = pow(light_color * base_color, 0.8 / cos_theta_d);
    float ntrt = (1.0f / PI) * 2.6 * exp(2 * 2.6 * (cos_phi - 1));
    s += ktrt * ttrt * mtrt * ftrt * ntrt;

    s += ambient_color;

    /*
    for (int p = 0; p<= 0; ++p)
    {
        float mp = Mp(BETA[p] * BETA[p], theta_i, theta_o - ALPHA[p]);
        float3 np = float3(0.0f, 0.0f, 0.0f);

        float3 lst_value;
        for (float h = -1.0f; h <= 1.0f + 1e-20f; h += NP_CALC_STEP) {
            //Ap
            float3 Ap;
            if (p == 0) {
                float a = fresnel(ETA, cos_half_io);
                Ap = float3(a, a, a);
            }
            else {
                float f = fresnel(ETA, cos_theta_d * sqrt(1 - h * h));
                float3 T = exp(-2 * miu_prime * (2 - pow2(h) / pow2(ETA_PRIME)));
                Ap = pow2(1 - f) * pow(f, p - 1) * pow(T, p);
            }

            //Dp
            float gamma_i = asin(h);
            float gamma_t = asin(h / ETA_PRIME);
            float phi_0 = phi - 2 * p * gamma_t - 2 * gamma_i + p * PI;
            //limit to the -PI~PI
            phi_0 = fmod(phi_0 + PI, PI2) + PI2;
            phi_0 -= PI2 * step(phi_0, PI2);
            phi_0 -= PI;
            float Dp = g(BETA[p], phi_0);

            if (h + 1e-10f <= -1.0f)
                lst_value = Dp * Ap;
            else {
                float3 value = Dp * Ap;
                np += (value + lst_value) * 0.5f * NP_CALC_STEP;
                lst_value = value;
            }
        }
        np *= 0.5f;

        s += k[p] * light_color * mp * np;
    }
    */

    return half4(s, 1.0f);
}