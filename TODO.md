# TODO

- [x] README 增加「参数矩阵」展示图：行 = chroma，列 = 测试图案（竖条 / 棋盘 / 斜纹），
      标注固定项（refraction / bezel / mapScale）。单张“最美效果图”无法说明参数区间，
      评审者看不出上限在哪里。生成入口：`python scripts/shoot_lab.py "chroma=1.4,1.8,2.2,2.6&refr=220&bezel=0.07" lab-strong.png`
- [x] 定版后同步更新 `docs/preview.png`、`docs/optics.png`、`docs/compare.png`，README 三处引用一起改。
- [x] 记录最终参数（chroma / refraction / bezel）到 README 的「调参建议」，避免下次又从默认值开始试。
