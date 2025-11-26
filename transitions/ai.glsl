// =====================================================================
//  Cyberpunk Glitch Transition (赛博朋克故障风转场)
//  Author: AI Assistant (Based on gl-transitions format)
// =====================================================================

// 自定义参数 (可以在 Python 的 CUSTOM_PARAMS 中调整)
uniform float strength = 0.5; //(整体故障强度)
uniform float speed = 10.0;    // (故障抖动速度)

// 辅助函数：生成伪随机数 (基于坐标)
float rand(vec2 co) {
    return fract(sin(dot(co.xy, vec2(12.9898, 78.233))) * 43758.5453);
}

// 辅助函数：生成块状噪声 (用于横向撕裂)
float noise(vec2 p) {
    vec2 ip = floor(p);
    vec2 u = fract(p);
    u = u * u * (3.0 - 2.0 * u);
    float res = mix(
        mix(rand(ip), rand(ip + vec2(1.0, 0.0)), u.x),
        mix(rand(ip + vec2(0.0, 1.0)), rand(ip + vec2(1.0, 1.0)), u.x),
        u.y);
    return res * res;
}

vec4 transition(vec2 uv) {
    // --- 参数设置 ---
    // 如果你在 Python 里没传这些 uniform，这里使用默认值
    // 强度曲线：先慢后快达到顶峰，然后迅速归零
    // 在 0.5 处达到最大值 1.0
    float current_strength = 0.5; // 默认值，如果传了 uniform strength 会被覆盖
    // current_strength = strength; // 如果有 uniform 就取消注释

    float current_speed = 10.0; // 默认速度
    // current_speed = speed; // 如果有 uniform 就取消注释
    
    // 计算故障强度曲线：在 0.5 处最强，两头弱
    float glitchAmount = smoothstep(0.0, 0.5, progress) * (1.0 - smoothstep(0.5, 1.0, progress));
    glitchAmount = pow(glitchAmount, 2.0) * current_strength * 2.0;

    // --- 1. 计算横向撕裂位移 (Displacement) ---
    // 使用噪声生成随机偏移量
    float time = progress * current_speed;
    // 主要撕裂
    float split = noise(vec2(uv.y * 10.0, time)) * glitchAmount * 0.2;
    // 次要高频抖动
    float split2 = noise(vec2(uv.y * 50.0, time * 5.0)) * glitchAmount * 0.05;
    
    // 应用位移到 X 轴
    vec2 dis_uv = uv;
    dis_uv.x += (split + split2) * (rand(vec2(uv.y, time)) - 0.5) * 2.0;

    // --- 2. RGB 色彩分离 (Chromatic Aberration) ---
    // 偏移量随故障强度增加
    float rgbOffset = glitchAmount * 0.05;
    
    // 分别采样 R, G, B 通道
    // 红色通道向左偏，蓝色通道向右偏，绿色通道在中间
    float r_sample = getFromColor(dis_uv + vec2(rgbOffset, 0.0)).r;
    float g_sample = getFromColor(dis_uv).g;
    float b_sample = getFromColor(dis_uv - vec2(rgbOffset * 1.5, 0.0)).b;
    vec3 fromCol = vec3(r_sample, g_sample, b_sample);

    // 对 ToColor 做同样的处理 (为了切换时的连贯性)
    float r_sample_t = getToColor(dis_uv + vec2(rgbOffset, 0.0)).r;
    float g_sample_t = getToColor(dis_uv).g;
    float b_sample_t = getToColor(dis_uv - vec2(rgbOffset * 1.5, 0.0)).b;
    vec3 toCol = vec3(r_sample_t, g_sample_t, b_sample_t);

    // --- 3. 切换逻辑 (Hard Cut) ---
    // 在 0.5 处瞬间切换，而不是平滑混合
    vec3 finalCol = mix(fromCol, toCol, step(0.5, progress));

    // --- 4. 发光与过曝效果 (Bloom / Flash) ---
    // 在转场最剧烈时增加亮度
    float flash = glitchAmount * 1.5;
    // 增加对比度和亮度，模拟发光
    finalCol = (finalCol - 0.5) * (1.0 + flash * 0.5) + 0.5;
    finalCol += vec3(flash * 0.3, flash * 0.1, flash * 0.5); // 加一点蓝紫色调的光

    // 添加扫描线纹理 (Scanlines) - 可选
    // finalCol *= 0.9 + 0.1 * sin(uv.y * 800.0);

    return vec4(finalCol, 1.0);
}