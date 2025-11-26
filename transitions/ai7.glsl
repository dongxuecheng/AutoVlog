// ====================================================
//  Angular Slice (多边形碎片切割)
// ====================================================

// 2D 旋转函数
vec2 rotate(vec2 v, float a) {
    float s = sin(a);
    float c = cos(a);
    mat2 m = mat2(c, -s, s, c);
    return m * v;
}

vec4 transition(vec2 uv) {
    // 1. 参数
    float count = 5.0; // 切割成多少块
    float smoothness = 0.5;
    float angle = 0.5; // 切割角度
    
    // 2. 将 UV 旋转以便切割
    vec2 p = uv - 0.5;
    p = rotate(p, angle);
    p += 0.5;
    
    // 3. 计算每个像素属于哪一个“切片” (ID)
    float pr = smoothstep(-smoothness, 0.0, p.x - progress * (1.0 + smoothness));
    
    // 这里做一个更有趣的效果：
    // 不仅仅是简单的 wipe，而是让不同的切片有不同的速度
    float sliceID = floor(p.y * count);
    
    // 随机速度偏移
    float offset = sin(sliceID * 5.0) * 0.5; // -0.5 ~ 0.5
    
    // 计算带偏移的进度
    // 有的切片切得快，有的切得慢
    float local_progress = clamp(progress * 1.5 + offset * progress - 0.2, 0.0, 1.0);
    
    // 4. 位移画面 (Slide)
    // 前一个画面向左飞，后一个画面从右飞入
    vec2 uv1 = uv + vec2(local_progress, 0.0);
    vec2 uv2 = uv + vec2(local_progress - 1.0, 0.0);
    
    // 5. 采样
    vec4 c1 = getFromColor(uv1);
    vec4 c2 = getToColor(uv2);
    
    // 6. 分割线发光 (可选)
    // 检测是否在切片边缘
    // float line = abs(p.x - local_progress);
    // float glow = 1.0 - smoothstep(0.0, 0.02, line);
    
    // 7. 混合
    // 使用简单的硬切割，因为我们要的是碎片感
    // 这里我们判断：如果 uv1 跑出去了，就显示 c2
    
    // 为了更精致，我们使用 smoothstep 混合
    // 这里的逻辑是：根据 x 轴的位置决定显示哪个
    float mixVal = step(p.x, local_progress);
    
    // 反转一下逻辑：
    // mixVal = 1 表示已经切过去了
    
    vec4 finalCol = mix(c1, c2, mixVal);
    
    // 加上暗角增加立体感
    float vign = length(vec2(0.5) - uv);
    finalCol.rgb *= (1.0 - vign * 0.3);
    
    return finalCol;
}