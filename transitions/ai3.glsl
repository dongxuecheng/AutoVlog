// ====================================================
//  Liquid Meltdown (液态熔化)
// ====================================================

// 辅助：伪随机噪声
float noise(vec2 st) {
    return fract(sin(dot(st.xy, vec2(12.9898,78.233))) * 43758.5453123);
}

vec4 transition(vec2 uv) {
    // 1. 制造波浪扭曲
    // progress * 2.5 让波浪随时间向下移动
    float wave = sin(uv.y * 10.0 + progress * 10.0) * 0.05; 
    float wave2 = sin(uv.x * 20.0 + progress * 20.0) * 0.02;
    
    // 2. 扭曲 UV
    vec2 dist_uv = uv + vec2(wave, wave2 * (1.0 - progress));
    
    // 3. 计算熔化阈值
    // 这里的噪声让边缘看起来参差不齐，像液滴
    float melting_edge = uv.y + noise(vec2(uv.x * 20.0, 0.0)) * 0.2;
    
    // 阈值随 progress 变化：从下往上还是从上往下取决于 progress 的方向
    // 这里做成 "画面A向下流走" 的效果
    float threshold = 1.0 - progress * 1.5 + 0.25; 
    
    // 4. 混合逻辑
    bool is_liquid = melting_edge > threshold;
    
    // 计算发光边缘 (Burn Edge)
    float edge_width = 0.05;
    float in_edge = smoothstep(threshold, threshold + edge_width, melting_edge) * smoothstep(threshold + edge_width * 2.0, threshold + edge_width, melting_edge);
    
    vec4 colorA = getFromColor(dist_uv);
    vec4 colorB = getToColor(uv); // B 画面保持静止或者轻微扭曲
    
    vec4 finalCol = is_liquid ? colorB : colorA;
    
    // 添加发光边 (橙红色火光)
    vec3 burnColor = vec3(1.0, 0.6, 0.2) * 2.0; 
    finalCol.rgb += burnColor * in_edge;
    
    return finalCol;
}