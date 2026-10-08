::ILANG
[TYPE:instructions][PROJECT:vps-deals][LANG:zh]
::STATE{@PROJECT, role:官方VPS方案与优惠静态站, runtime:Python标准库}
::OBJECTIVE{公开来源可核验 确定性更新 无推理无付费API}
::RULE{唯一配置来源 .ilang/site.ilang；修改厂商必须改变抓取与渲染}
::RULE{允许 修复解析器 更新模板 检查证据 运行测试 更新官方来源}
::RULE{数据必须由scraper.py读取公开来源；遵守robots；失败关闭该来源价格}
::RULE{报价必须绑定真实方案 币种 周期 来源 抓取时间；普通定价不是优惠}
::RULE{部署后仅使用实际确认的Pages生产地址；不得猜canonical域名}
::BOUNDARY{never:编价格 编佣金 编截止日 绕反爬 买粉 刷量 品牌词竞价 cookie注入 自买自推|scope:permanent}
::RULE{联盟链接仅在用户已获批准且明确配置后启用；必须披露}
