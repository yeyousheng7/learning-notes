# Spring Cloud 微服务调用链与治理复习笔记

## 1. 整体知识地图

本次学习从 Spring Cloud 常见组件出发，围绕一条完整的微服务调用链展开：

```text
Client
  ↓
Gateway
  ↓
LoadBalancer
  ↓
Service A
  ↓
OpenFeign
  ↓
LoadBalancer
  ↓
Service B
```

旁边还有 Nacos 提供：

```text
Nacos
├── 服务注册
├── 服务发现
└── 配置中心
```

调用过程中又会遇到：

```text
超时
↓
重试
↓
幂等
↓
熔断
↓
降级
```

面对流量问题：

```text
限流
```

面对排障与监控：

```text
Trace ID / Span
Logs / Metrics / Traces
```

后续又扩展到了：

```text
线程池
连接池
排队
背压
```

这些已经属于微服务性能与稳定性基础，不再是 Spring Cloud 组件本身的核心主线。

---

## 2. 服务间调用的最基本问题

### 2.1 不使用 Spring Cloud 也能调用其他服务

假设有两个服务：

```text
Service A：订单服务
Service B：用户服务
```

A 完全可以直接请求：

```text
GET http://192.168.1.20:8081/users/123
```

因此：

> Spring Cloud 组件不是为了让“原本不可能的服务调用”变得可能，而是解决服务地址动态变化、多实例选择、统一治理等问题。

真正的问题在于服务地址往往不稳定。

例如：

```text
user-service
├── B1 192.168.1.20:8081
├── B2 192.168.1.21:8081
└── B3 192.168.1.22:8081
```

这时调用方需要面对：

- 到底请求哪个实例？
- 某实例挂了怎么办？
- 新增实例后怎么发现？
- IP 变化后怎么同步？
- 多个实例如何分散请求？

于是出现了：

```text
服务注册 / 发现
+
负载均衡
```

---

## 3. OpenFeign：声明式 HTTP 客户端

### 3.1 基本作用

典型写法：

```java
@FeignClient(name = "user-service")
public interface UserClient {

    @GetMapping("/users/{id}")
    UserDTO getUser(@PathVariable Long id);
}
```

业务代码：

```java
UserDTO user = userClient.getUser(123L);
```

虽然看起来像普通 Java 方法调用，但本质仍然是：

```text
Service A
↓ HTTP
Service B
```

OpenFeign 可以先理解为：

> 根据 Java 接口声明，帮助构造并发起远程 HTTP 调用。

它会根据：

- `@FeignClient`
- `@GetMapping`
- `@PostMapping`
- 参数
- 路径

等信息构造请求。

#### 核心记忆

```text
OpenFeign
→ “怎么描述、怎么发起远程 HTTP 调用”
```

---

### 3.2 OpenFeign 不负责什么

容易误解为：

> OpenFeign 自己知道 `user-service` 对应哪个 IP，并决定请求哪个实例。

实际上需要进一步依赖服务发现和负载均衡。

更准确的链路：

```text
Feign 解析：
我要调用 user-service
GET /users/123
        ↓
服务发现
        ↓
得到 B1 / B2 / B3
        ↓
LoadBalancer
        ↓
选择某个实例
        ↓
真正发送 HTTP 请求
```

因此：

```text
OpenFeign ≠ 服务发现
OpenFeign ≠ LoadBalancer
```

但它们可以集成在一起。

---

### 3.3 Feign 是否每个服务都有

不是。

更准确地说：

> 哪个服务需要主动调用其他服务，哪个服务才可能需要 Feign。

例如：

```text
Order Service
↓
User Service
```

Order Service 可能需要 Feign。

如果 User Service 不主动调用任何其他服务，则它不一定需要 Feign。

---

## 4. Spring Cloud LoadBalancer：客户端负载均衡

### 4.1 作用

服务发现拿到：

```text
user-service
├── B1
├── B2
└── B3
```

LoadBalancer 负责：

> 根据某种策略，从候选实例中选择一个。

例如轮询：

```text
请求1 → B1
请求2 → B2
请求3 → B3
请求4 → B1
...
```

因此：

```text
LoadBalancer
→ “这些实例里到底选谁？”
```

---

### 4.2 负载均衡不等于绝对平均

假设：

```text
B1：10 ms
B2：10 ms
B3：2 s
```

即使轮询让三者都收到约 1/3 请求：

```text
B1 ← 1/3
B2 ← 1/3
B3 ← 1/3
```

请求数量看起来平均，但 B3 很慢，实际压力并不平均。

因此：

> “请求数平均”不等于“真实负载平均”。

会话中提到过的策略包括：

```text
轮询
随机
权重
最少连接
根据响应时间
```

本次学习不深入这些策略的具体实现。

---

### 4.3 为什么叫客户端负载均衡

这里的“客户端”不是浏览器，而是：

> 当前这一跳中，主动发起请求的一方。

例如：

```text
A → B
```

则：

```text
A = 客户端
B = 服务端
```

LoadBalancer 运行在 A 一侧：

```text
Service A
   │
   ├─ 已知 B1 / B2 / B3
   │
   ├─ 本地选择 B2
   ↓
  B2
```

因此称为：

```text
Client-Side Load Balancing
```

---

### 4.4 与 Nginx 式负载均衡的区别

传统形式：

```text
Client
  ↓
Nginx
  ↓
B1 / B2 / B3
```

客户端只知道 Nginx。

而 Spring Cloud LoadBalancer：

```text
Service A
↓
服务发现
↓
获得 B1 / B2 / B3
↓
本地 LoadBalancer
↓
选 B2
↓
直接请求 B2
```

---

### 4.5 LoadBalancer 是否每个服务都有

和 Feign 一样，不是“每个服务强制存在”。

如果某个服务需要调用其他多实例服务，它可能使用 LoadBalancer。

例如：

```text
A → B
```

A 可能使用 LoadBalancer。

如果：

```text
B → C
```

那么 B 在这一跳又变成客户端，也可能使用自己的 LoadBalancer。

---

## 5. Nacos：注册中心与配置中心

### 5.1 服务注册

服务实例启动后，会向 Nacos 注册。

例如：

```text
服务名：user-service
IP：10.0.0.1
端口：8080
状态：healthy
```

多个实例形成：

```text
user-service
├── 10.0.0.1:8080
└── 10.0.0.2:8080
```

#### 注意

注册的是：

> 服务实例

而不是：

- Java 类
- Controller
- 某个方法

---

### 5.2 为什么需要注册

调用方不应该自己维护：

```java
List<String> userServers = List.of(
    "10.0.0.1:8080",
    "10.0.0.2:8080"
);
```

因为实例可能：

```text
挂掉
新增
重启
IP 变化
```

注册中心的核心价值是：

> 维护当前有哪些服务实例可用。

---

### 5.3 健康检查 / 心跳

实例注册后不能永久认为它存活。

可以粗略理解为：

```text
B1 ──“我还活着”──→ Nacos
B1 ──“我还活着”──→ Nacos
B1 ──“我还活着”──→ Nacos
```

如果长时间得不到健康信息：

```text
Nacos
↓
判断 B1 不健康
↓
不再将其作为正常实例提供
```

本次会话只要求理解思想：

> 注册中心除了保存实例，还需要维护实例存活状态。

---

### 5.4 服务发现

Service A 不知道：

```text
user-service
```

对应什么 IP。

通过服务发现得到：

```text
user-service
↓
10.0.0.1:8080
10.0.0.2:8080
```

服务发现通常得到的是：

> 一组候选实例

而不是一个最终地址。

之后再交给 LoadBalancer 选择。

---

### 5.5 易错点：注册中心 ≠ 配置中心

本次学习中曾出现误解：

> “Gateway 通过向配置中心读取配置获取 `order-service` 实例。”

这个理解不准确。

正确区分：

#### 注册中心 / 服务发现

回答：

```text
“服务在哪里？”
```

例如：

```text
order-service
├── Order1
└── Order2
```

#### 配置中心

回答：

```text
“服务应该怎么运行？”
```

例如：

```yaml
payment:
  timeout: 3000

feature:
  coupon-enabled: true
```

最适合记住的一句话：

> 注册中心管地址，配置中心管配置。

或者：

> 注册中心解决“找谁”，配置中心解决“怎么配”。

---

## 6. Nacos 配置中心

### 6.1 为什么有 `application.yml` 还需要配置中心

单体项目中：

```yaml
server:
  port: 8080

spring:
  datasource:
    url: jdbc:mysql://localhost:3306/app
```

直接放本地没有问题。

但微服务可能存在多个服务、多个实例：

```text
order-service
├── Order1
├── Order2
└── Order3
```

如果配置都散落在各实例：

```text
Order1/application.yml
Order2/application.yml
Order3/application.yml
```

修改配置会很麻烦。

配置中心的思想：

> 把原本散落在各服务中的配置集中管理。

---

### 6.2 配置中心的基本作用

Nacos 中可能有：

```text
order-service 配置

timeout = 3000
coupon-enabled = true
max-order-count = 20
```

多个实例共享：

```text
             Nacos 配置中心
                   │
        ┌──────────┼──────────┐
        ↓          ↓          ↓
     Order1     Order2     Order3
```

---

### 6.3 服务如何拿配置

可以粗略理解为：

```text
Service 启动
↓
连接 Nacos
↓
读取自己的配置
↓
加载到 Spring Environment
↓
应用使用配置
```

例如：

```java
@Value("${feature.coupon-enabled}")
private boolean couponEnabled;
```

或者：

```java
@ConfigurationProperties(prefix = "feature")
```

本质仍然是 Spring 应用读取配置，只是配置来源发生变化。

---

### 6.4 动态修改

配置中心的一个重要价值：

```text
Nacos 修改配置
↓
服务获取新配置
↓
运行时使用新的配置
```

例如：

```text
recommendation-enabled = false
```

可以用于：

```text
功能开关
限流阈值
超时时间
灰度参数
业务参数
```

---

### 6.5 边界：不是所有配置都能运行时直接生效

例如：

```text
server.port
```

即使在配置中心修改，也不能简单认为：

```text
8080 → 9090
```

应用运行中一定能直接无缝修改监听端口。

因此：

> 使用配置中心 ≠ 所有配置都能热更新。

有些配置：

```text
启动时读取一次
```

有些配置：

```text
可以运行时刷新
```

---

## 7. Gateway：微服务统一入口

### 7.1 Gateway 在哪里

典型位置：

```text
客户端
  ↓
Gateway
  ↓
后端服务
```

例如：

```text
浏览器 / App
      ↓
   Gateway
      ↓
 ┌────┼────┐
 ↓    ↓    ↓
用户 订单 商品
服务 服务 服务
```

因此 Gateway 可以理解为：

> 介于客户端与后端服务之间的统一入口。

---

### 7.2 Gateway 与 Nginx 的关系

粗略理解：

```text
Nginx
≈ 通用反向代理 / 网络入口

Gateway
≈ 微服务专用的应用级反向代理 / API 入口
```

两者都有：

```text
反向代理
路由转发
负载均衡
```

但关注层次不同。

#### Nginx 更偏

```text
网络入口
反向代理
静态资源
TLS/HTTPS
基础负载均衡
```

#### Gateway 更偏

```text
微服务路由
JWT 鉴权
权限
限流
服务发现
Spring 生态集成
```

---

### 7.3 Gateway 可以和 Nginx 同时存在

例如：

```text
Client
↓
Nginx / Cloud LB
↓
Gateway
↓
微服务
```

它们不是必然竞争关系。

更适合这样理解：

```text
Nginx / Cloud LB
→ 更偏基础设施入口

Gateway
→ 更偏 API / 微服务入口

Feign + LoadBalancer
→ 更偏服务内部调用
```

---

### 7.4 Gateway 是否类似服务端负载均衡

从外部客户端看：

```text
Client
↓
Gateway
↓
Order1 / Order2 / Order3
```

Gateway 很像服务端负载均衡器。

但是从这一跳内部实现看：

```text
Gateway → Order Service
```

Gateway 自己就是调用方，因此它内部使用的 LoadBalancer 仍属于：

> 客户端负载均衡。

因此两种说法不冲突：

```text
从外部客户端视角：
Gateway ≈ 服务端负载均衡入口

从 Gateway → 下游这一跳：
Gateway 使用客户端负载均衡
```

---

## 8. 多层负载均衡

一个完整架构可能是：

```text
Client
   ↓
Nginx / Cloud LB
   ↓
Gateway1 / Gateway2 / Gateway3
   ↓
Gateway 内部 LoadBalancer
   ↓
Service A 集群
   ↓
Service A 内部 Feign + LoadBalancer
   ↓
Service B 集群
```

不同层负责不同选择：

```text
Nginx / Cloud LB
→ 选择哪个 Gateway

Gateway
→ 选择哪个目标服务实例

Service A 的 LoadBalancer
→ A 调 B 时选择哪个 B
```

因此：

> 负载均衡不一定只发生一次，每一跳都可能有自己的实例选择。

---

## 9. Gateway 的 Route、Predicate、Filter

### 9.1 总体关系

可以先记：

```text
请求
↓
Predicate：这条请求是否匹配某条路由？
↓
Route：匹配后整体路由规则是什么？
↓
Filter：转发前后做哪些处理？
↓
目标服务
```

---

### 9.2 Route

一条 Route 可以理解为：

> 什么请求，经过什么处理，最终去哪里。

例子：

```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: order-route
          uri: lb://order-service
          predicates:
            - Path=/api/orders/**
```

含义：

```text
Route ID：
order-route

Predicate：
Path=/api/orders/**

URI：
lb://order-service
```

即：

> `/api/orders/**` 请求转发给 `order-service`。

---

### 9.3 Predicate

Predicate 本质上是：

> 条件判断。

可以粗略理解为：

```java
boolean matches(Request request);
```

例如：

```text
Path=/api/orders/**
```

请求：

```text
GET /api/orders/123
```

匹配。

请求：

```text
GET /api/users/1
```

不匹配。

本次会话提到 Predicate 可根据：

```text
Path
Method
Header
Host
Query 参数
```

等进行匹配。

也可以组合，例如：

```text
Path = /api/orders/**
AND
Method = GET
```

---

### 9.4 Filter

Filter 用于：

> 对请求或响应进行额外处理。

会话中提到的例子：

```text
加 Header
删 Header
改 Path
鉴权
记录日志
限流
```

Filter 既可以处理：

```text
请求转发前
```

也可以处理：

```text
响应返回客户端前
```

---

### 9.5 `StripPrefix`

例如外部路径：

```text
/api/orders/123
```

内部接口：

```text
/orders/123
```

可以使用：

```text
StripPrefix=1
```

形成：

```text
/api/orders/123
↓
/orders/123
```

完整过程：

```text
① Gateway 收到请求

② Predicate 匹配：
   /api/orders/**

③ Filter：
   StripPrefix=1

④ uri:
   lb://order-service

⑤ 服务发现：
   Order1 / Order2

⑥ LoadBalancer：
   选择 Order2

⑦ 请求 Order2 /orders/123
```

---

### 9.6 GatewayFilter 与 GlobalFilter

#### GatewayFilter

只对某些 Route 生效。

例如：

```text
只对 order-route 添加某个 Header
```

#### GlobalFilter

对经过 Gateway 的所有请求生效。

例如：

```text
JWT
日志
Trace ID
```

---

## 10. Gateway Filter、Servlet Filter、HandlerInterceptor

这三个容易混淆。

总体层级：

```text
Client
↓
Gateway
↓
GatewayFilter / GlobalFilter
↓
某个微服务
↓
Servlet Filter
↓
DispatcherServlet
↓
HandlerInterceptor
↓
Controller
```

---

### 10.1 Servlet Filter

典型位置：

```text
HTTP 请求
↓
Servlet Container
↓
Filter
↓
DispatcherServlet
↓
Controller
```

例如：

```java
class JwtAuthenticationFilter extends OncePerRequestFilter {
    @Override
    protected void doFilterInternal(...) {
        // 解析 JWT
        // 设置 SecurityContext
        // filterChain.doFilter(...)
    }
}
```

适合：

```text
JWT / Security
CORS
日志
请求包装
通用请求处理
```

---

### 10.2 HandlerInterceptor

位置更靠近 Controller：

```text
Filter
↓
DispatcherServlet
↓
Interceptor
↓
Controller
```

因此它更接近 Spring MVC Handler，可以更自然地知道：

```text
当前 Controller
当前方法
HandlerMethod
```

例如处理某个 Controller 方法上的注解。

---

### 10.3 Gateway Filter

它属于另一个独立 Gateway 服务：

```text
Client
↓
Gateway Application
↓
Order Service Application
```

它主要看到的是：

```text
HTTP Method
Path
Header
Query
Body
目标服务
```

而不是：

```text
OrderController#createOrder()
```

---

### 10.4 作用范围对比

```text
Gateway Filter / GlobalFilter
→ 整个微服务系统入口

Servlet Filter
→ 单个 Spring Boot 应用入口

HandlerInterceptor
→ Spring MVC Controller 层
```

一个很好用的判断方式：

```text
“所有微服务外部请求统一处理”
→ Gateway

“当前 Spring Boot 服务所有请求统一处理”
→ Filter

“某些 Controller / 方法执行前后处理”
→ Interceptor
```

---

## 11. JWT 鉴权与身份传递

### 11.1 最简单的做法

Gateway 验证 JWT 后得到：

```text
userId = 123
role = USER
```

然后转发：

```http
X-User-Id: 123
X-Role: USER
```

下游读取这些 Header。

---

### 11.2 易错点：普通身份 Header 不能直接相信

攻击者可能直接请求：

```text
Order Service
```

并伪造：

```http
X-User-Id: 1
X-Role: ADMIN
```

因此：

> `X-User-Id` 本身没有天然安全性。

Gateway 至少应该：

```text
删除客户端原本传入的身份 Header
↓
根据已经验证过的 JWT
重新写入身份 Header
```

---

### 11.3 下游服务最好不能被公网直接访问

更合理的结构：

```text
Internet
↓
Gateway
↓
内部网络
↓
Order / User / Payment
```

而不是：

```text
Internet
├→ Gateway
├→ Order Service
└→ Payment Service
```

这样可以降低绕过 Gateway 伪造身份的风险。

---

### 11.4 JWT 一路透传

一种思路：

```text
Client
↓ JWT
Gateway
↓ JWT
Order Service
↓ JWT
Payment Service
```

每个服务都可以：

```text
验证 JWT
↓
解析 userId / role
↓
建立自己的 SecurityContext
```

这样业务代码继续从安全上下文获取身份。

---

### 11.5 核心安全原则

本次学习反复强调：

> 身份应该来自经过验证的 token / 安全上下文，而不是普通业务参数。

不要让客户端或模型直接决定：

```text
userId
role
```

---

## 12. Feign 的 JWT 透传

### 12.1 `RequestInterceptor`

Order Service 调 Payment Service：

```java
paymentClient.createPayment(...);
```

Feign 默认不会自动把当前 HTTP 请求的：

```http
Authorization: Bearer ...
```

复制到新的远程请求。

可以使用：

```java
RequestInterceptor
```

在 Feign 发请求前修改请求。

简化代码：

```java
@Bean
public RequestInterceptor authRequestInterceptor() {
    return template -> {
        ServletRequestAttributes attributes =
                (ServletRequestAttributes) RequestContextHolder.getRequestAttributes();

        if (attributes == null) {
            return;
        }

        String authorization =
                attributes.getRequest()
                          .getHeader("Authorization");

        if (authorization != null) {
            template.header("Authorization", authorization);
        }
    };
}
```

核心逻辑：

```text
读取当前请求 Authorization
↓
加入 Feign 新请求 Authorization
```

形成：

```text
Client
↓ JWT
Gateway
↓ JWT
Order
↓ JWT
Payment
```

---

### 12.2 业务参数不应该承载当前用户身份

不推荐把当前用户身份当普通业务参数：

```java
paymentClient.createPayment(userId, orderId);
```

更倾向于：

```java
paymentClient.createPayment(orderId);
```

Payment Service 自己从经过验证的安全上下文取得：

```text
currentUserId
```

---

### 12.3 边界：没有 HTTP 请求上下文时怎么办

例如：

```text
定时任务
MQ 消费
异步任务
后台任务
```

这时：

```java
RequestContextHolder.getRequestAttributes()
```

可能是：

```text
null
```

因为根本不存在当前用户 HTTP 请求。

因此：

> “透传当前用户 JWT”只适用于确实存在用户请求上下文的调用。

后台服务调用不应该硬造一个用户 JWT。

---

### 12.4 异步线程的上下文问题

例如：

```java
CompletableFuture.runAsync(() -> {
    paymentClient.createPayment(...);
});
```

原线程：

```text
Tomcat Thread A
└─ RequestContext
```

异步后：

```text
Thread Pool Thread B
└─ ?
```

Thread B 不一定自动拥有原请求上下文。

因此简单依赖：

```java
RequestContextHolder
```

在异步场景可能失效。

这引出了：

```text
Context Propagation
```

即上下文传播问题。

---

### 12.5 Feign `RequestInterceptor` 与 MVC `HandlerInterceptor`

不要因为名字都有 Interceptor 就混淆。

#### Feign `RequestInterceptor`

作用于：

```text
Service A
↓
Feign 准备发送 HTTP
↓
RequestInterceptor
↓
Service B
```

属于：

> 出站请求拦截。

#### MVC `HandlerInterceptor`

作用于：

```text
HTTP 请求进入服务
↓
DispatcherServlet
↓
HandlerInterceptor
↓
Controller
```

属于：

> 入站 MVC 请求拦截。

---

## 13. 用户身份与服务身份

例如：

```text
Order Service → Payment Service
```

Payment Service 可能想知道两个不同的问题：

```text
1. 当前用户是谁？
2. 发起请求的服务是谁？
```

它们不是同一回事：

```text
用户身份：
userId = 123

服务身份：
caller = order-service
```

本次会话只提出了这一区分，没有继续展开具体实现。

---

## 14. 服务实例故障、超时与重试

### 14.1 注册中心状态存在时间差

假设：

```text
B1
B2
B3
```

B2 突然挂掉。

可能发生：

```text
t0：B2 正常
t1：B2 崩溃
t2：调用方仍认为 B2 可用
t3：LoadBalancer 选中 B2
t4：请求失败
t5：注册中心 / 客户端更新状态
```

因此：

> 服务发现可以降低调用失效实例的概率，但不能保证永远不会调用到坏实例。

---

### 14.2 健康 ≠ 每次业务请求都成功

即使注册中心认为：

```text
B1 healthy
```

也可能出现：

```text
CPU 100%
数据库连接池满
GC 卡住
线程池满
下游服务异常
```

因此：

> 注册中心认为实例健康，不等于当前这次业务请求一定成功。

---

### 14.3 常见失败表现

#### 连接拒绝

```text
Connection refused
```

可以粗略理解为：

> IP 能到，但目标端口没有服务监听。

#### 连接超时

```text
connect timeout
```

表示：

> TCP 连接没能在规定时间内建立。

#### 读取超时

```text
read timeout
```

表示：

```text
连接可能已经建立
请求也可能已经发过去
但是迟迟没有收到响应
```

---

### 14.4 易错点：请求失败 ≠ 自动重试

练习中曾回答：

> “选中已挂掉的 Pay1 后，可能会重试。”

更准确的顺序是：

```text
请求失败
↓
如果系统配置了重试策略
↓
才可能重试
```

所以：

> 失败是可能发生的结果；重试只是某种处理策略。

---

## 15. 超时、重试与幂等

假设第一次：

```text
A → B2
```

B2 实际已经创建订单，但响应丢失：

```text
数据库：
order_id = 1001
```

A 只看到：

```text
timeout
```

于是重试：

```text
A → B3
```

B3 又创建：

```text
order_id = 1002
```

最终：

```text
用户只操作一次
↓
系统产生两个业务结果
```

因此：

> 超时不能证明服务端没有执行。

重试前必须考虑：

```text
接口是否幂等
```

尤其非幂等操作可能造成：

```text
重复订单
重复支付
重复业务副作用
```

---

## 16. 熔断、降级、限流

### 16.1 熔断

场景：

```text
A → B → C
```

C 很慢，大量 B 的线程都在等 C：

```text
B
├── thread1 等 C
├── thread2 等 C
├── thread3 等 C
└── ...
```

最终可能：

```text
C 出问题
↓
B 被拖死
↓
A 调 B 也超时
↓
故障扩散
```

熔断的思想：

> 下游明显异常时，暂时不要继续调用它，避免故障继续扩散。

---

### 16.2 熔断器三个状态

#### CLOSED

```text
B → C
```

正常放行请求，同时统计成功、失败、慢调用等情况。

#### OPEN

```text
B ─X→ C
```

不再调用下游，直接失败或走 fallback。

#### HALF_OPEN

等待一段时间后，允许少量试探请求：

```text
测试成功
→ CLOSED

测试仍失败
→ OPEN
```

---

### 16.3 降级

当主功能不可用时：

> 返回一个次优但仍可接受的结果。

例如推荐服务挂了：

```text
个性化推荐
↓ 失败
热门推荐
```

这里：

```text
熔断
→ 决定“还要不要调用下游”

降级
→ 决定“不调用以后给用户什么”
```

---

### 16.4 限流

当系统承受能力是：

```text
1000 req/s
```

却突然来了：

```text
10000 req/s
```

如果全接可能造成：

```text
线程池满
数据库连接池满
CPU 满
服务崩溃
```

限流的思想：

> 主动限制通过的请求数量，保护系统。

例如：

```text
10000 req/s
      ↓
   限流器
   ↓     ↓
1000    9000
通过     拒绝
```

---

### 16.5 三者区分

```text
限流
→ 请求太多，少接一点

熔断
→ 下游明显异常，暂时别调

降级
→ 主功能做不了，返回次优结果
```

三个判断问题：

```text
限流：
“别人是不是打我打得太狠了？”

熔断：
“我调用的下游是不是已经不行了？”

降级：
“下游不行以后，我还能给用户什么？”
```

---

## 17. 限流算法

### 17.1 固定窗口

例如：

```text
每秒最多 100 个请求
```

时间切成：

```text
[0s,1s) [1s,2s) [2s,3s)
```

每个窗口独立计数。

超过 100：

```text
拒绝
```

进入下一窗口：

```text
counter = 0
```

#### 问题：窗口边界突刺

例如：

```text
0.9s ~ 1.0s：100 个
1.0s ~ 1.1s：100 个
```

两个固定窗口都合法，但：

```text
0.9s ~ 1.1s
只有 0.2 秒
却进入 200 个请求
```

因此：

> 每个固定窗口不超限，不等于任意连续 1 秒都不超限。

---

### 17.2 滑动窗口

不看固定自然秒，而看：

> 当前时刻往前一段时间内有多少请求。

例如当前：

```text
12:00:01.500
```

统计：

```text
12:00:00.500
~
12:00:01.500
```

如果已有 100 个：

```text
当前请求 → 拒绝
```

对比：

```text
固定窗口
→ 按预先切好的时间块统计

滑动窗口
→ 统计当前时刻往前一段时间
```

---

### 17.3 令牌桶

设：

```text
桶容量 = 100 token
生成速度 = 10 token/s
```

每个请求需要一个 token：

```text
有 token
→ 通过

没 token
→ 限制
```

令牌可以在空闲时积累。

例如桶里攒满：

```text
100 token
```

突然来 80 个请求：

```text
80 个可以立即通过
```

因此令牌桶特点：

```text
短时间允许 burst
长期限制 rate
```

---

### 17.4 漏桶

漏桶更像：

```text
请求
 ↓↓↓
┌─────────┐
│ 请求队列 │
└────┬────┘
     ↓
固定速率流出
```

例如：

```text
桶容量 = 100
流出速度 = 10 req/s
```

请求先进入桶中，再以固定速度向下游释放。

桶满后：

```text
新请求 → 丢弃 / 拒绝
```

核心作用：

> 把不均匀的突发流量削平。

---

### 17.5 令牌桶与漏桶的区别

最重要的一句话：

```text
令牌桶
→ 控制“能不能现在通过”

漏桶
→ 控制“以多快的速度往外处理”
```

例如瞬间来 50 个请求：

#### 令牌桶

如果 token 足够：

```text
50 个可能立即通过
```

#### 漏桶

```text
50 个先排队
↓
按固定速度逐渐释放
```

---

### 17.6 易错点：令牌桶和漏桶不是默认一起使用

本次会话专门确认过：

> 两者通常应先理解为两种不同方案，而不是天然搭配。

当然工程上可以组合：

```text
令牌桶
↓
先判断是否接收请求
↓
漏桶 / 队列
↓
再平滑送给下游
```

但这不是默认关系。

---

## 18. Gateway 限流

Gateway 是很自然的统一限流位置：

```text
Client
↓
Gateway
├── 鉴权
├── 限流
├── 路由
└── 负载均衡
↓
Service
```

例如：

```text
某 IP：
10 req/s

某用户：
100 req/min
```

还可以不同接口不同规则：

```text
GET /products
1000 req/s

POST /orders
100 req/s

POST /login
10 req/s
```

但：

> 限流不一定只能放 Gateway。

还可以存在：

```text
Order Service 自己限流
```

或者：

```text
Order Service → Payment Service
```

这一跳做保护。

---

## 19. Nacos 故障时系统会怎样

### 19.1 Nacos 作为注册中心挂掉

调用方通常不会每个请求都实时问 Nacos：

```text
“payment-service 有哪些实例？”
```

否则注册中心本身会变成严重瓶颈。

调用方一般会维护：

```text
本地服务实例列表 / 缓存
```

所以 Nacos 突然挂掉时，已经运行的服务可能仍然知道：

```text
Pay1
Pay2
```

并继续请求。

---

### 19.2 真正问题：实例列表会变旧

例如 Nacos 挂后：

```text
Pay1 ✅
Pay2 ❌
Pay3 ✅ 新启动
```

调用方本地还认为：

```text
Pay1
Pay2
```

于是：

- 可能继续请求已挂的 Pay2
- 不知道新加入的 Pay3

因此：

> 注册中心故障的核心问题之一，是服务拓扑无法及时更新。

---

### 19.3 新实例注册也会受影响

例如：

```text
Pay3 启动
↓
Nacos 不可用
```

其他服务可能无法及时发现 Pay3。

---

### 19.4 Nacos 作为配置中心挂掉

如果服务已经加载：

```yaml
payment:
  timeout: 3000
```

Nacos 挂掉后：

> 已经加载的配置通常不会突然消失。

服务仍然可以继续使用：

```text
timeout = 3000
```

但：

```text
动态配置更新
```

会受到影响。

---

### 19.5 运行中故障与启动时故障要区分

#### 已经运行

```text
服务已启动
↓
已有实例列表
已有配置
↓
Nacos 挂
```

通常还有一定生存能力。

#### 服务正在启动

```text
Service 启动
↓
需要从 Nacos 获取必要配置
↓
Nacos 不可用
```

可能：

```text
启动失败
```

或者只能使用本地 / 缓存配置。

因此不能简单回答：

```text
“Nacos 挂了，系统能不能运行？”
```

更准确的思路：

> 要区分已经运行的服务与新启动的服务。

---

### 19.6 Nacos 自身也需要高可用

如果只有：

```text
Nacos × 1
```

则存在单点风险。

会话中提到生产环境通常会考虑：

```text
Nacos1
Nacos2
Nacos3
```

本次学习不深入集群内部一致性算法。

---

## 20. 控制面与数据面

### 20.1 Nacos 更偏控制面

Nacos 主要告诉系统：

```text
服务在哪里
配置是什么
实例状态怎么样
```

可以粗略理解为：

> 控制系统“应该怎么运行”。

---

### 20.2 Gateway 在真正业务请求链路里

业务请求：

```text
Client
↓
Gateway
↓
Order Service
↓
User Service
```

请求 body、header、订单数据等会真正经过这些组件。

因此 Gateway 更接近：

> 数据面中的 in-path component。

---

### 20.3 一个重要区别

错误理解：

```text
A → Nacos → B
```

正确理解：

```text
A ─────────→ B
↑
Nacos 只是提前告诉 A：
“B 在哪里”
```

因此：

> Nacos 不是业务请求代理。

这与 Gateway / Nginx 明显不同。

---

### 20.4 为什么控制面故障不一定立即拖死业务

如果 A 已经知道：

```text
B1
B2
B3
```

即使 Nacos 暂时挂掉：

```text
A → B2
```

可能仍能继续。

但如果 Gateway 是唯一入口：

```text
Client
↓
Gateway ❌
```

业务请求第一跳就断了。

可以粗略概括：

```text
控制面故障
→ 更容易影响“变化能力”

数据面故障
→ 更直接影响“请求处理能力”
```

---

## 21. Trace ID 与 Span

### 21.1 Trace ID 是什么

假设：

```text
Client
↓
Gateway
↓
Order Service
↓
Payment Service
↓
MySQL
```

如果没有统一标识，各服务日志很难确认是否属于同一次请求。

于是给整条调用链一个唯一 ID：

```text
Trace ID = abc123
```

日志：

```text
[traceId=abc123] Gateway 收到请求
[traceId=abc123] Order 开始创建订单
[traceId=abc123] Payment 调用失败
```

因此：

> Trace ID 标识一次完整分布式调用链。

可以记：

```text
Trace ID
→ 一次完整请求链的身份证
```

---

### 21.2 Trace ID 为什么需要透传

例如：

```text
Gateway      traceId=abc123
↓
Order        traceId=abc123
↓
Payment      traceId=abc123
```

这样才能跨服务关联日志。

这与 JWT 的“沿调用链传播”形式相似，但用途不同。

---

### 21.3 Span ID

Trace 表示：

```text
一次完整请求
```

Span 表示：

```text
请求中的某一小段调用
```

例如：

```text
Trace abc123

Gateway → Order
Span = s1

Order → Payment
Span = s2

Order → MySQL
Span = s3
```

因此：

```text
Trace
├── Span1
├── Span2
└── Span3
```

---

### 21.4 父子关系

只有 Trace ID 仍然不能知道谁调用谁。

例如：

```text
Gateway
Order
User
Payment
```

可能是：

```text
Gateway
└── Order
    ├── User
    └── Payment
```

也可能是：

```text
Gateway
└── Order
    └── User
        └── Payment
```

所以 Span 还需要父子关系。

本次会话提到每个 Span 可以有：

```text
spanId
parentSpanId
开始时间
结束时间
耗时
状态
服务名
操作名
```

于是完整 Trace 可以形成树。

---

### 21.5 Trace ID 与 JWT 不同

```text
JWT
→ 安全上下文
→ “这个人是谁？”

Trace Context
→ 可观测性上下文
→ “这次请求是哪条链？”
```

因此：

> Trace ID 不能替代鉴权。

---

## 22. Logs、Metrics、Traces

### 22.1 三者区别

```text
Logs
→ 具体发生了什么

Metrics
→ 系统整体运行得怎么样

Traces
→ 某一次请求具体怎么走
```

---

### 22.2 Logs

适合回答：

> 某一次具体失败发生了什么？

例如：

```text
traceId=abc123
payment timeout
orderId=10086
```

信息很细，但难以直接观察整体趋势。

---

### 22.3 Metrics

常见数字型指标：

```text
QPS = 500
错误率 = 1.2%
CPU = 65%
P99 延迟 = 800ms
```

适合：

```text
监控
告警
趋势分析
判断系统是否异常
```

---

### 22.4 Traces

例如：

```text
Gateway
└── Order
    └── Payment
        └── MySQL
```

可以看到：

```text
请求经过哪些服务
每一段耗时多少
哪里失败
```

---

### 22.5 典型排障流程

```text
Metrics
↓
发现异常

Traces
↓
定位哪一段调用有问题

Logs
↓
查看具体异常原因
```

---

## 23. QPS、P95、P99、错误率

### 23.1 QPS

QPS：

```text
Queries Per Second
```

在本次 Web 服务讨论中可以粗略理解为：

> 每秒请求数 / 请求吞吐量。

例如：

```text
1 秒处理 1000 个 HTTP 请求
→ QPS ≈ 1000
```

会话中也指出：

> 实际系统可能区分 QPS、RPS、TPS，但本次不继续展开。

---

### 23.2 QPS 高不一定有问题

例如：

```text
QPS = 10000
P99 = 50ms
错误率 = 0.01%
```

可能运行得很好。

而：

```text
QPS = 10000
P99 = 8s
错误率 = 30%
```

说明系统已经明显异常。

因此：

> 单个指标不能独立判断系统健康。

---

### 23.3 P95 / P99

将请求延迟从快到慢排序。

如果：

```text
P95 = 300ms
```

表示：

```text
95% 请求 ≤ 300ms
5% 请求 > 300ms
```

如果：

```text
P99 = 1s
```

表示：

```text
99% 请求 ≤ 1s
1% 请求 > 1s
```

---

### 23.4 为什么不能只看平均值

假设：

```text
99 个请求 = 10ms
1 个请求 = 10s
```

平均延迟约：

```text
110ms
```

看起来还不错，但实际上有用户等待了：

```text
10 秒
```

所以平均值可能掩盖：

```text
尾部慢请求
```

这就是为什么常看：

```text
P95
P99
P999
```

---

### 23.5 错误率

基本形式：

```text
错误率 =
失败请求数 / 总请求数
```

例如：

```text
10000 请求
100 个失败
→ 1%
```

但“什么算失败”需要看监控定义。

会话中举过：

```text
5xx
超时
连接失败
某些业务错误
```

是否都算系统错误，要看口径。

---

## 24. P99 高不一定是业务代码本身慢

一个重要性能公式：

```text
Latency
=
Queueing Time
+
Service Time
```

即：

```text
延迟
=
排队时间
+
真正处理时间
```

例如真正业务执行：

```text
50ms
```

但用户看到：

```text
2s
```

额外时间可能来自：

```text
等线程
等数据库连接
等下游响应
```

---

## 25. 线程池、连接池与排队

### 25.1 线程池排队

假设：

```text
最大工作线程 = 100
```

同时进来：

```text
500 个请求
```

则：

```text
前 100 个立即执行
其余 400 个排队
```

即使单个请求真正只需要：

```text
50ms
```

后面的请求仍可能因为排队导致 P99 很高。

---

### 25.2 数据库连接池排队

例如：

```text
Web 线程 = 200
DB 连接池 = 20
```

100 个请求同时访问数据库：

```text
20 个拿到连接
80 个等待
```

即使 SQL：

```text
10ms
```

接口延迟仍可能很高。

因此：

> 慢 SQL 和慢请求不是同一回事。

---

### 25.3 下游慢会反过来拖慢上游

例如：

```text
A → B
```

A 自己只需要：

```text
20ms
```

但 B：

```text
2s
```

如果 A 是阻塞等待：

```text
A 的线程
↓
一直等 B
```

B 一慢：

```text
A 的线程大量被占用
↓
A 线程池开始排队
↓
A 自己也变慢
```

这就是故障扩散的一种形式。

---

## 26. 线程池和连接池不是越大越好

### 26.1 线程太多

如果系统真正瓶颈是：

```text
CPU
数据库连接
磁盘 IO
下游服务
锁竞争
```

把线程从：

```text
100
```

改成：

```text
1000
```

不意味着吞吐量直接提高 10 倍。

还可能增加：

```text
上下文切换
线程内存占用
资源竞争
```

---

### 26.2 线程池很大但 DB 连接池很小

例如：

```text
Order Service 线程 = 1000
DB 连接池 = 20
```

则：

```text
20 个线程拿到连接
980 个等待
```

只是制造更多等待。

---

### 26.3 连接池也不能无限扩大

如果 MySQL 只能较稳定处理：

```text
100 个活跃连接
```

却开：

```text
1000 connections
```

大量 SQL 同时执行，可能导致：

```text
CPU 争抢
Buffer Pool 争抢
磁盘 IO 增加
锁竞争增加
```

最终可能：

```text
吞吐没提高多少
延迟反而变大
```

因此：

> 并发度应该受控，而不是无限放大。

---

### 26.4 与 semaphore 的类比

数据库连接池可以粗略类比：

```text
Semaphore permits = 20
```

访问数据库：

```text
acquire()
↓
拿到 permit
↓
使用连接
↓
release()
```

第 21 个请求需要等待。

因此连接池本质上也体现：

> 对有限资源的并发访问进行控制。

---

### 26.5 排队有时是在保护系统

如果数据库稳定承受：

```text
50 并发
```

那么：

```text
50 个执行
100 个排队
```

可能比：

```text
150 个全部同时执行
```

更好。

因为后者可能让所有请求一起变慢。

---

### 26.6 队列也不能无限大

如果：

```text
服务处理能力 = 100 req/s
输入 = 1000 req/s
```

每秒积压：

```text
+900
```

无限队列只会导致：

```text
等待越来越多
内存越来越高
延迟越来越大
最终失败
```

因此：

> 无限队列不是解决过载的方法，只是在延迟失败。

---

### 26.7 易错优化：只会调大池子

错误思路：

```text
线程池满
↓
100 → 1000

DB 连接池满
↓
20 → 200
```

最终可能把瓶颈一直向下游推：

```text
MySQL CPU 100%
P99 上升
锁等待增加
```

真实容量并没有提高。

更合理的思路：

```text
延迟高
↓
是不是排队？
↓
排在哪里？
↓
为什么资源不够？
↓
池子太小？
下游太慢？
流量太大？
```

---

## 27. 背压 Backpressure

### 27.1 核心思想

假设：

```text
A → B
```

A 产生：

```text
1000 条/s
```

B 只能处理：

```text
100 条/s
```

如果 A 一直不管 B：

```text
每秒积压 900
```

最终：

```text
队列越来越长
↓
内存越来越高
↓
延迟越来越大
↓
OOM / 超时 / 崩溃
```

背压的核心：

> 当下游处理不过来时，要有办法让上游减慢发送速度。

---

### 27.2 压力反向传播

数据流：

```text
A → B → C
```

背压：

```text
A ← B ← C
```

例如：

```text
C：
“我现在只能再接 10 个”

B：
减少继续向 C 发送

B 压力变大后：
也可能继续让 A 慢下来
```

---

### 27.3 背压与限流

#### 限流

更强调：

> 主动规定最多接受多少流量。

例如：

```text
Gateway：
最多 1000 req/s
```

#### 背压

更强调：

> 根据下游当前消费能力反馈上游，让生产速度与消费速度匹配。

可以先记：

```text
限流
→ 固定 / 规则化地控制流量

背压
→ 根据消费能力反馈流量
```

---

### 27.4 队列不能解决长期生产大于消费

例如：

```text
Producer = 1000/s
Consumer = 100/s
```

增加一个：

```text
容量 = 100000
```

的大队列。

因为：

```text
每秒 +900
```

大约 111 秒后队列仍会满。

因此：

> 队列只能吸收短时突发，不能解决长期输入速率大于输出速率。

最终必须从以下方向处理：

```text
让 Producer 慢一点
让 Consumer 快一点
增加 Consumer
丢弃部分数据
降低处理复杂度
```

---

## 28. 本次会话中的核心易错点汇总

### 28.1 把服务发现说成“读取配置”

错误理解：

```text
Gateway 通过读取配置中心获得 Order1 / Order2
```

正确：

```text
Gateway 通过服务发现获得 order-service 的实例列表
```

原因：

```text
注册中心
→ 管实例

配置中心
→ 管配置
```

---

### 28.2 认为 OpenFeign 自己负责选服务实例

错误：

```text
Feign 决定请求 B1 / B2
```

更准确：

```text
Feign
→ 描述并发起 HTTP 调用

服务发现
→ 提供候选实例

LoadBalancer
→ 选择最终实例
```

---

### 28.3 “选中坏实例后会重试”

不够准确。

正确顺序：

```text
先发生调用失败
↓
如果配置了重试
↓
才可能重试
```

---

### 28.4 Gateway 是不是服务端负载均衡

不能只回答“是”或“不是”。

```text
从外部客户端看：
Gateway 很像服务端负载均衡入口

从 Gateway → Service 这一跳：
Gateway 是客户端，
内部 LoadBalancer 属于客户端负载均衡
```

---

### 28.5 “注册中心认为健康 = 请求一定成功”

错误。

即使：

```text
healthy
```

也可能：

```text
线程池满
连接池满
CPU 高
GC 卡住
下游异常
```

---

### 28.6 “超时 = 服务端没有执行”

错误。

可能是：

```text
请求未到达
服务端执行失败
服务端已执行但响应丢失 / 超时
```

因此自动重试必须考虑幂等。

---

### 28.7 “使用配置中心 = 所有配置都能热更新”

错误。

有些配置：

```text
启动时读取
```

有些配置：

```text
运行时可以刷新
```

不能一概而论。

---

### 28.8 “Nacos 挂了 = 所有业务立刻停止”

不准确。

需要区分：

```text
已经运行的服务
新启动的服务
```

已经运行的服务可能还有：

```text
本地实例列表
已经加载的配置
```

但注册发现更新、动态配置能力会受影响。

---

### 28.9 “X-User-Id 这种 Header 可以直接作为可信身份”

错误。

普通 Header 可以被客户端伪造。

身份应来自：

```text
经过验证的 token
安全上下文
可信内部传递机制
```

---

### 28.10 Trace ID 可以做鉴权

错误。

```text
Trace ID
→ 标识调用链

JWT
→ 标识并验证用户身份
```

用途完全不同。

---

### 28.11 令牌桶和漏桶是默认组合

错误。

应先理解为两种独立方案：

```text
令牌桶
→ 允许一定突发

漏桶
→ 把输出削平
```

可以组合，但不是天然配套。

---

### 28.12 线程池 / 连接池越大越好

错误。

更大的池子可能只是：

```text
增加等待
增加上下文切换
把压力继续向下游推
增加数据库竞争
```

调池子前应该先定位真实瓶颈。

---

## 29. 本次会话中做过的复习题

场景：

```text
Client
  ↓
Gateway
  ↓
Order Service
  ↓
Payment Service
```

实例：

```text
order-service
├── Order1
└── Order2

payment-service
├── Pay1
└── Pay2
```

所有服务均注册到 Nacos。

客户端：

```http
POST /orders
```

Order 创建订单后，再调用 Payment 创建支付单。

---

### 29.1 问题

1. 谁负责把 `/orders` 转发到 `order-service`？
2. `Order1` / `Order2` 谁负责选择？
3. Gateway 怎么知道 `order-service` 有哪些实例？
4. OpenFeign 主要负责什么？
5. `Pay1` / `Pay2` 谁负责选择？
6. Pay1 已挂但注册中心尚未更新时会怎样？
7. 超时后自动重试为什么要谨慎？
8. Payment 大量失败后暂时不再调用它叫什么？
9. 不调用 Payment 后返回“订单已创建，支付稍后处理”叫什么？
10. Gateway 主动拒绝超出承载能力的请求叫什么？

---

### 29.2 复盘答案

```text
1. Gateway

2. LoadBalancer
   具体选哪个实例取决于负载均衡策略和当前状态

3. 通过服务发现从注册中心获取 order-service 实例列表
   不是“读取配置中心”

4. OpenFeign：
   根据声明完成远程 HTTP 调用

5. LoadBalancer
   具体是 Pay1 还是 Pay2 取决于实际选择结果

6. 请求可能：
   连接失败 / 超时 / 其他失败
   如果配置了重试，才可能进一步重试

7. 因为：
   超时不能证明第一次没有执行
   非幂等接口重试可能产生重复业务副作用

8. 熔断

9. 降级 / fallback

10. 限流
```

---

## 30. 最终压缩记忆表

```text
Gateway
→ 外部统一入口、路由、过滤、鉴权、限流等

Nacos 注册中心
→ 服务在哪里

Nacos 配置中心
→ 服务怎么配

OpenFeign
→ 怎么声明并发起服务间 HTTP 调用

LoadBalancer
→ 多个实例里选谁

超时
→ 不代表服务端没有执行

重试
→ 必须考虑幂等

熔断
→ 下游异常，暂时别调

降级
→ 主功能不可用，返回次优结果

限流
→ 请求太多，少放一些

Trace ID
→ 一次完整请求链的标识

Span
→ 调用链中的一段

Logs
→ 具体发生了什么

Metrics
→ 系统整体情况

Traces
→ 某次请求具体怎么走

QPS
→ 吞吐量

P95 / P99
→ 尾部延迟

Latency
→ Queueing Time + Service Time

Backpressure
→ 下游处理不过来时，让上游减慢
```
