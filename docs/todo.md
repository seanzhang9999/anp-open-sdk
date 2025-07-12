# sdk层
 - 双向token
 - 数据库支持
 - 对browser插件的支持
 - anp连接支持sse/ws认证
 - did及服务地址的模版化问题
 - 支持多域名
 - 重构example
 - 配置文件按example处理
 
# framework层
 - did.json ad.json的动态配置处理
 - 统一装饰器+封装器
 - 统一调用器+搜索器
 - 调用器的mcp封装
 - 基于调用器接口的llm自动编码通过装饰器再发布
 - 托管增加sse/ws——对接到auth_server预留接口 实现托管远端did
 - auth_midddleware 只是身份认证，授权应该放到agent的路由点，
   - 一方面知道自己有什么api，
   - 一方面知道自己是谁对方是谁
 - 授权逻辑框架（面向企业/个人/团队）
 - 个人的多节点的智能体怎么互联
   - 一个群组都搞定
   - 群组里的二次授权