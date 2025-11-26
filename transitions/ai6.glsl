// ====================================================
//  Cinematic Film Burn (电影胶片烧灼)
// ====================================================

// 简单的噪声函数 (Value Noise)
float hash(vec2 p) { return fract(1e4 * sin(17.0 * p.x + p.y * 0.1) * (0.1 + abs(sin(p.y * 13.0 + p.x)))); }

float noise(vec2 x) {
    vec2 i = floor(x);
    vec2 f = fract(x);
    float a = hash(i);
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(a, b, u.x) + (c - a) * u.y * (1.0 - u.x) + (d - b) * u.x * u.y;
}

// 分形布朗运动 (生成云雾状纹理)
float fbm(vec2 x) {
    float v = 0.0;
    float a = 0.5;
    vec2 shift = vec2(100.0);
    // 旋转矩阵
    mat2 rot = mat2(cos(0.5), sin(0.5), -sin(0.5), cos(0.50));
    for (int i = 0; i < 4; ++i) {
        v += a * noise(x);
        x = rot * x * 2.0 + shift;
        a *= 0.5;
    }
    return v;
}

vec4 transition(vec2 uv) {
    // 1. 画面本身的切换 (简单的滑动 Slide)
    // 你可以改成 Zoom 或者直接 Mix，这里用 Slide 配合烧灼很好看
    vec2 p = uv;
    float x = progress;
    p.x -= x * 0.2; // 画面轻微移动
    
    vec4 c1 = getFromColor(p);
    vec4 c2 = getToColor(uv); // 后一个画面静止或微动
    
    // 2. 生成烧灼纹理 (Burn Texture)
    // 纹理随时间快速移动，模拟光斑掠过
    float burn_pattern = fbm(uv * 5.0 + vec2(progress * 15.0, 0.0));
    
    // 3. 定义烧灼曲线
    // 在 progress 中间时，光斑最亮
    float burn_intensity = 1.0 - abs(progress - 0.5) * 2.0;
    burn_intensity = smoothstep(0.0, 1.0, burn_intensity); 
    
    // 4. 定义光斑颜色 (橙红色 -> 暖白)
    vec3 burn_color = vec3(1.0, 0.6, 0.2) * 2.0; // 高亮橙色
    
    // 5. 混合
    // 基础混合
    vec4 finalCol = mix(c1, c2, smoothstep(0.3, 0.7, progress));
    
    // 叠加光斑 (Additive Blending)
    // 只有当噪声值超过某个阈值时才显示光斑
    float burn_mask = smoothstep(0.4, 0.8, burn_pattern * burn_intensity + 0.2);
    
    finalCol.rgb += burn_color * burn_mask;
    
    // 稍微增加一点整体曝光
    finalCol.rgb += vec3(burn_intensity * 0.2);
    
    return finalCol;
}