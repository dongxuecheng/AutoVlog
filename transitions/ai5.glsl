// ====================================================
//  Data Stream Stretch (数据流拉伸)
// ====================================================

// 随机函数
float rand(vec2 co){
    return fract(sin(dot(co.xy ,vec2(12.9898,78.233))) * 43758.5453);
}

vec4 transition(vec2 uv) {
    // 1. 核心参数
    float strength = 0.5; // 拉伸强度
    float frequency = 20.0; // 噪声条纹的密度
    
    // 2. 动画曲线：在 0.5 处达到峰值
    float phase = progress;
    float intensity = 1.0 - abs(phase - 0.5) * 2.0; // 0 -> 1 -> 0
    intensity = pow(intensity, 3.0); // 让峰值更尖锐
    
    // 3. 生成基于 Y 轴的条纹噪声
    float noiseWave = rand(vec2(floor(uv.y * frequency), 1.0));
    
    // 4. 计算位移 (Displacement)
    // 根据噪声和强度，向左或向右拉伸像素
    float displacement = (noiseWave - 0.5) * intensity * strength;
    
    // 5. RGB 分离 (Chromatic Aberration)
    // 红色通道偏移多一点，蓝色通道偏移少一点
    vec2 uvR = uv + vec2(displacement * 1.5, 0.0);
    vec2 uvG = uv + vec2(displacement, 0.0);
    vec2 uvB = uv + vec2(displacement * 0.5, 0.0);
    
    // 6. 采样
    // 这里的逻辑是：如果 intensity 很大，我们就拉伸画面。
    // 在 progress 0.5 处瞬间切换源
    vec4 c1R = getFromColor(uvR); vec4 c1G = getFromColor(uvG); vec4 c1B = getFromColor(uvB);
    vec4 c2R = getToColor(uvR);   vec4 c2G = getToColor(uvG);   vec4 c2B = getToColor(uvB);
    
    vec4 color1 = vec4(c1R.r, c1G.g, c1B.b, 1.0);
    vec4 color2 = vec4(c2R.r, c2G.g, c2B.b, 1.0);
    
    // 7. 混合逻辑
    // 并不是简单的淡入淡出，而是"被拉伸的像素"飞出去，新的进来
    // 在中间时刻，画面因为拉伸变得模糊
    
    if (progress < 0.5) {
        return color1;
    } else {
        return color2;
    }
    
    // 也可以加一点发光让拉伸处更亮
    // return mix(color1, color2, step(0.5, progress));
}