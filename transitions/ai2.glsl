// ====================================================
//  Cross Zoom Blur (极速变焦模糊)
// ====================================================

// 自定义参数
uniform float strength = 0.4; // (模糊强度)

vec4 transition(vec2 uv) {
    // 参数默认值
    float strength = 0.4; 
    
    // 缓动曲线：让运动先慢后快再慢
    // Linear interpolation is boring, use a curve
    float PI = 3.141592653589793;
    float phase = progress < 0.5 ? 16.0 * pow(progress, 5.0) : 1.0 - pow(-2.0 * progress + 2.0, 5.0) / 2.0;

    vec2 center = vec2(0.5, 0.5);
    vec2 texCoord = uv - center;
    
    // 采样循环 (模拟模糊)
    // 采样次数越多越平滑，但性能消耗越大。20次是平衡点。
    vec4 c = vec4(0.0);
    float total = 0.0;
    
    for (float t = 0.0; t <= 20.0; t++) {
        float percent = (t + rand(vec2(uv.x, uv.y + progress))) / 20.0; // 加入随机抖动消除条纹
        float weight = 4.0 * (percent - percent * percent);
        
        // 计算缩放偏移
        // 在 0~0.5 缩小(Zoom Out)，在 0.5~1.0 放大(Zoom In)
        float current_scale = mix(1.0, 0.2, phase * 2.0 * (0.5 - abs(progress - 0.5))); 
        
        // 应用模糊偏移
        vec2 sample_uv = center + texCoord * current_scale * (1.0 - strength * percent * (0.5 - abs(progress - 0.5)));
        
        // 混合：前半段采 A，后半段采 B
        vec4 sampleColor = mix(getFromColor(sample_uv), getToColor(sample_uv), step(0.5, progress));
        
        // 越边缘模糊越重
        c += sampleColor * weight;
        total += weight;
    }
    
    return c / total;
}