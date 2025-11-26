// ====================================================
//  Space Vortex (旋涡吸入)
// ====================================================

vec4 transition(vec2 uv) {
    // 归一化坐标到 -1 ~ 1
    vec2 p = uv - 0.5;
    
    // 计算角度和距离
    float len = length(p);
    float angle = atan(p.y, p.x);
    
    // 动画曲线：转场中间扭曲最大
    float phase = progress; 
    // 旋转力度：随距离衰减，越中心转得越快
    float rotate_strength = (1.0 - len) * 15.0 * sin(progress * 3.14159);
    
    // 新的角度
    float new_angle = angle + rotate_strength;
    
    // 极坐标转回笛卡尔坐标
    vec2 new_p;
    float zoom = 1.0;
    
    // 加上缩放效果：中间时刻缩小
    if (progress < 0.5) {
        zoom = 1.0 - progress; // 缩小
    } else {
        zoom = progress;       // 放大
    }
    // 防止 zoom 变成 0
    zoom = max(0.1, zoom);
    
    new_p.x = len * zoom * cos(new_angle);
    new_p.y = len * zoom * sin(new_angle);
    
    vec2 new_uv = new_p + 0.5;
    
    // 边界检测：如果扭曲出去了，显示黑色或者镜像
    if (new_uv.x < 0.0 || new_uv.x > 1.0 || new_uv.y < 0.0 || new_uv.y > 1.0) {
        return vec4(0.0, 0.0, 0.0, 1.0); // 黑洞边缘
    }
    
    // 混合
    return mix(
        getFromColor(new_uv),
        getToColor(new_uv),
        step(0.5, progress)
    );
}