import moderngl

try:
    # -------------------------------------------------------------
    # 关键修改：添加 backend='egl'
    # 这告诉 ModernGL："不要去找 X11 显示器，直接跟显卡驱动对话"
    # -------------------------------------------------------------
    ctx = moderngl.create_context(standalone=True, backend="egl")

    print("\n✅ ModernGL Context Created Successfully (EGL Mode)!")
    print("-" * 40)

    # 获取显卡信息
    info = ctx.info
    print(f"Vendor:   {info['GL_VENDOR']}")
    print(f"Renderer: {info['GL_RENDERER']}")
    print(f"Version:  {info['GL_VERSION']}")
    print("-" * 40)

    # 检查是否是 NVIDIA
    renderer_name = info["GL_RENDERER"].lower()
    if "nvidia" in renderer_name:
        print("🚀 Success! Running on NVIDIA GPU via EGL.")
    elif "llvmpipe" in renderer_name:
        print("⚠️ Warning! Running on CPU Software Rendering.")
        print("   Checking Docker flags...")

except Exception as e:
    print("\n❌ Error creating context:")
    print(e)
    print("-" * 40)
    print("Troubleshooting Tips:")
    print("1. Ensure 'libegl1' is installed in Dockerfile.")
    print("2. Ensure run command includes '--gpus all'.")
    print("3. Try setting ENV variable: MODERNGL_BACKEND=egl")
