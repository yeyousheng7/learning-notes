# JVM 第一阶段学习笔记：运行时内存、对象生命周期、GC 与类加载

## 1. JVM 的整体运行模型

Java 程序并不是直接把源码编译成某个平台的机器码再执行，而是先编译成 JVM 字节码，再由 JVM 负责运行。

基本链路：

```text
.java
 ↓ javac
.class 字节码
 ↓ ClassLoader
JVM 加载
 ↓
运行时数据区
 ↓
执行引擎
 ↓
解释执行 / JIT
 ↓
机器码
 ↓
CPU
```

JVM 本身不是操作系统，而是运行在操作系统之上的一个进程环境：

```text
Java 应用
   ↓
JVM / java 进程
   ↓
操作系统
   ↓
硬件
```

例如：

```bash
java -jar knowledge-hub.jar
```

可以粗略理解为：

```text
Linux
 └── java 进程
      ├── JVM
      ├── Spring Boot
      ├── Java Heap
      ├── Java 线程
      └── GC
```

### JVM 的几个主要组成

```text
JVM
├── Class Loader
├── Runtime Data Area
├── Execution Engine
└── Native Method Interface
```

- `Class Loader`：把 `.class` 加载进 JVM。
- `Runtime Data Area`：Java 程序运行时使用的内存区域。
- `Execution Engine`：执行字节码。
- Native 相关机制：支持 Java 调用本地 C/C++ 等实现。

### 解释执行与 JIT

JVM 可以对字节码进行解释执行：

```text
字节码1
↓
执行
↓
字节码2
↓
执行
```

也可以在运行过程中发现热点代码，将其编译成机器码：

```text
字节码
 ↓ JIT
机器码
```

本轮学习还没有继续深入 JIT，只建立了这一层总体认识。

---

## 2. JVM 运行时数据区

运行时数据区首先可以按“线程私有”和“线程共享”划分。

```text
线程私有
├── 程序计数器
├── Java 虚拟机栈
└── 本地方法栈

线程共享
├── Java 堆
└── 方法区
```

这个划分和 Java 多线程运行直接相关：

- 每个线程执行到哪里、当前有哪些方法调用，是线程自己的。
- 堆中的对象可能被多个线程共同访问，因此属于共享区域。

---

## 3. 程序计数器

程序计数器用于记录当前线程执行到哪一条 JVM 指令。

可以类比 CPU 中的 PC 寄存器：

```text
Thread A
PC = 第 10 条指令

Thread B
PC = 第 50 条指令
```

每个线程必须有自己的执行位置，因此程序计数器属于线程私有区域。

---

## 4. Java 虚拟机栈与栈帧

### 4.1 方法调用与栈帧

每调用一个 Java 方法，会创建一个对应的栈帧并压入当前线程的 JVM 栈。

例如：

```java
void a() {
    b();
}

void b() {
    c();
}
```

执行到 `c()` 时可以理解为：

```text
Java 虚拟机栈

c 栈帧
--------
b 栈帧
--------
a 栈帧
```

方法返回时，对应栈帧出栈。

因此递归太深最终出现 `StackOverflowError` 的本质是：

> 方法调用不断产生栈帧，最终把 JVM 栈空间耗尽。

---

### 4.2 栈帧里的核心内容

本次学习主要关注：

```text
Stack Frame
├── 局部变量表 Local Variable Array
├── 操作数栈 Operand Stack
├── 动态链接 Dynamic Linking
└── 方法返回相关信息
```

---

### 4.3 局部变量表

例如：

```java
static int add(int a, int b) {
    int c = a + b;
    return c;
}
```

局部变量表可以粗略理解为：

```text
slot 0 → a
slot 1 → b
slot 2 → c
```

如果是实例方法，还可能包含 `this`。

方法参数本身也是当前方法的局部变量。

局部变量表按 `slot` 组织。当前会话只建立了“变量槽”的概念，没有继续深入具体布局细节。

---

### 4.4 操作数栈

JVM 字节码的执行模型主要基于操作数栈。

例如：

```java
int c = a + b;
```

可以粗略理解为：

```text
[]
↓ 加载 a
[3]
↓ 加载 b
[3, 5]
↓ add
[8]
↓ 保存到 c
[]
```

对应的一组类似字节码：

```text
iload_0
iload_1
iadd
istore_2
iload_2
ireturn
```

这体现了 JVM 作为“基于栈的虚拟机”的特点。

真实 CPU 通常使用寄存器模型，而 JVM 字节码层面主要使用操作数栈；最终仍然会映射到底层机器指令、寄存器和真实内存。

---

### 4.5 动态链接

`.class` 中很多方法引用最初不是一个固定内存地址，而是类似：

```text
User.work:()V
```

这样的符号引用。

运行时 JVM 需要将：

```text
“User.work 这个方法”
```

解析到真正可以调用的方法。

这就是动态链接相关工作的基本含义。

---

## 5. 栈、堆和对象引用

例如：

```java
void test() {
    int age = 20;
    User user = new User();
}
```

可以理解为：

```text
当前线程的栈

test 栈帧
├── age = 20
└── user = 引用 --------+
                       |
                       v

Java Heap
└── User 对象
```

关键区别：

- `user`：局部变量，位于当前方法栈帧中。
- `new User()` 创建的对象：主要位于堆中。

### 易错点：局部变量和常量池/方法区

曾经将：

```java
void work() {
    int count = 10;
}
```

里的 `count` 误判为“常量池 / 方法区”。

正确理解：

- `count` 是局部变量 → 当前线程的 JVM 栈。
- `10` 是字面量。
- “变量在哪里”和“字面量是什么”不是同一个问题。

---

## 6. Java 堆

Java 堆是线程共享区域，也是 GC 主要管理的区域。

大量对象：

```java
new User();
new Order();
new ArrayList<>();
```

主要都会进入堆。

### 堆为什么线程共享

例如两个线程都访问：

```text
Thread A ──┐
           ↓
        Counter
        count
           ↑
Thread B ──┘
```

如果多个线程共享同一个堆对象，就可能出现线程安全问题。

反过来，普通局部变量存在当前线程自己的栈帧中，一般具有天然的线程隔离性。

---

## 7. 方法区：类信息与对象状态

方法区主要保存类级别的信息，而不是每个具体对象自己的状态。

例如：

```java
class User {
    int age;

    void login() {}
}
```

类加载后，JVM 需要保存：

```text
User 类
├── 类名
├── 父类信息
├── 字段定义：age : int
├── 方法定义：login()
├── 方法字节码等
└── 运行时常量池
```

而具体对象：

```java
User a = new User();
User b = new User();
```

各自拥有自己的实例状态：

```text
User 对象 A
└── age = 20

User 对象 B
└── age = 35
```

### 易错点：字段定义和字段值

- `User 有一个 int age 字段` → 类结构信息 → 方法区。
- `某个 User 对象的 age = 20` → 对象状态 → 跟对象一起位于堆中。

### 方法区不等于“只存方法”

“方法区”这个名字容易让人误以为它只存 Java 方法。

本次学习中采用的理解是：

> 方法区主要用于保存类级元数据。

---

## 8. 方法区、PermGen 与 Metaspace

当前学习建立了以下层次：

- 方法区：JVM 规范层面的逻辑概念。
- Java 8 之后 HotSpot 中，方法区的很大一部分由 Metaspace 实现。
- Metaspace 使用本地内存。
- Java 7 及以前常见永久代 `PermGen` 的说法。

本轮没有继续深入 PermGen / Metaspace 的更细节实现。

---

## 9. 运行时常量池

`.class` 文件自身包含常量池，其中会记录一些符号信息，例如：

```text
"hello"
类名
方法名
字段名
方法描述符
```

类加载后，会建立对应的运行时常量池。

本轮没有深入常量池的具体二进制结构。

---

## 10. `new User()` 的对象创建过程

执行：

```java
User user = new User();
```

时，本次学习得到的主线是：

```text
检查 User 类是否已加载
↓
为对象分配内存
↓
对象字段零值初始化
↓
设置对象头等 JVM 信息
↓
执行字段初始化和构造方法
↓
得到对象引用
↓
赋给局部变量 user
```

---

### 10.1 内存分配

如果堆空间规整，可以通过类似“指针碰撞”的方式分配：

```text
[ 已使用 ][          空闲          ]
           ↑
          top
```

分配新对象后，只需要移动指针。

如果空闲内存比较碎，则需要类似空闲列表的思路记录哪些位置可用。

---

### 10.2 零值初始化

例如：

```java
class User {
    int age;
    boolean active;
    Object obj;
}
```

对象内存拿到后，会先得到默认值：

```text
age = 0
active = false
obj = null
```

### 易错点：成员变量与局部变量

成员变量：

```java
class User {
    int age;
}
```

可以有默认值。

局部变量：

```java
void test() {
    int x;
    System.out.println(x);
}
```

不能直接使用未初始化值。

---

### 10.3 对象头、实例数据和对齐填充

一个 Java 对象可以粗略理解成：

```text
Java Object
├── Object Header
├── Instance Data
└── Padding
```

本轮只认识概念：

- 对象头：JVM 管理对象需要的一些信息。
- 实例数据：对象字段本身的数据。
- 对齐填充：对象布局中的填充部分。

对象头可能和类信息、GC、锁、hashCode 等有关，但本轮没有继续深入 Mark Word 的位布局。

---

### 10.4 字段初始化和构造方法

例如：

```java
class User {
    int age = 18;

    User() {
        age = 20;
    }
}
```

可以理解为：

```text
分配内存
↓
age = 0
↓
字段初始化
age = 18
↓
构造方法
age = 20
```

---

## 11. 对象生命周期与 GC

### 11.1 不可达不等于立即释放

例如：

```java
void add() {
    User user = new User();
}
```

`add()` 返回后：

- `user` 局部变量随着栈帧出栈而消失。
- 如果没有其他引用指向该 `User` 对象，它会变成不可达。
- 不可达只是意味着“有资格被 GC 回收”，并不意味着立即释放。

---

## 12. 引用计数与可达性分析

### 12.1 引用计数的基本思想

引用计数法可以理解为：

```text
新增引用 → count++
引用消失 → count--
count = 0 → 回收
```

优势：

- 回收及时。
- 不需要每次从 Roots 扫描整个对象图。
- 如果排除循环引用问题，它是一种很自然的内存管理思路。

但成本会摊到每一次引用变化：

```java
a = b;
```

背后可能意味着：

```text
旧对象引用计数 -1
新对象引用计数 +1
```

在多线程场景下，计数修改还可能涉及原子操作和竞争。

因此可以把两类思路理解为：

```text
Tracing GC
→ 平时引用修改相对轻
→ GC 时集中做扫描工作

引用计数
→ 每次引用变化都维护计数
→ 回收可以更及时
```

---

### 12.2 循环引用问题

例如：

```text
A → B
↑   ↓
└───┘
```

外部已经无法访问 A/B，但：

```text
A 引用数 = 1
B 引用数 = 1
```

单纯引用计数无法判断它们已经无用。

### 易错点：STW 不能解决引用计数的循环依赖

曾出现“循环依赖确实 STW”的理解。

纠正：

> STW 只是让引用关系暂时不再变化，不能让 A/B 的引用计数自动变成 0。

要解决循环引用，仍然需要额外机制，例如类似可达性扫描 / cycle collector。

---

## 13. GC Roots 与可达性分析

JVM 主流思路是：

> 从一组 GC Roots 出发，沿引用关系遍历对象图。

只要对象从某个 Root 可达，就认为仍然存活。

典型示意：

```text
GC Root
   ↓
   A
  / \
 B   C
 |
 D
```

A、B、C、D 都可达。

而：

```text
X → Y
↑   ↓
└───┘
```

如果从任何 Root 都走不到 X/Y，则这一整组对象不可达。

---

### 13.1 GC Roots 为什么足够

一个对象如果当前程序还能访问到，它的引用一定来自某个“入口”，例如：

```text
线程栈中的引用
↓
A
```

或者：

```text
static 字段
↓
B
↓
A
```

因此 GC Roots 本质上代表 JVM 当前能够直接掌握的引用入口。

如果某个对象从所有 Root 都不可达，那么程序已经没有路径重新得到它的引用。

---

### 13.2 典型 GC Roots 来源

本次学习提到的主要包括：

- 当前线程栈中的引用。
- 静态字段持有的引用。
- JNI / Native 层持有的引用。

---

### 13.3 Java 也会内存泄漏

例如：

```java
static List<User> users = new ArrayList<>();
```

不断添加对象：

```text
GC Root
↓
static users
├── User1
├── User2
├── User3
└── ...
```

即使业务上已经不需要这些对象，只要引用还在，它们仍然是可达的，GC 就不能回收。

所以 Java 的典型内存泄漏不是“忘了 `free()`”，而是：

> 业务上已经没用的对象，仍然被长期存活的引用持有。

---

## 14. 可达性分析如何遍历完整对象图

把对象关系看成图：

```text
A → B → C
    ↓
    D
```

GC 可以维护“待扫描集合”和“已访问状态”。

例如：

```text
待扫描：[A]
```

扫描 A 后发现 B：

```text
已访问：A
待扫描：[B]
```

扫描 B 后：

```text
已访问：A, B
待扫描：[C, D]
```

直到待扫描集合为空。

这样，只要某对象从 Root 可达，最终都会被遍历到。

### 如何避免循环遍历

GC 可以维护类似 `visited` 的标记信息，例如 Mark Bitmap。

对于：

```text
A → B
↑   ↓
└───┘
```

A 已经标记后，再次遇到 A 不需要重复扫描，因此不会无限循环。

---

## 15. STW 与并发 GC

### 15.1 为什么最简单的方案是 STW

如果 GC 扫描对象图时，业务线程还在不停修改：

```text
A → B
```

突然变成：

```text
A 不再指向 B
C → B
```

遍历就会复杂很多。

因此最简单、最容易保证正确性的方式是：

```text
暂停所有 Java 业务线程
↓
GC 扫描
↓
对象引用关系暂时稳定
↓
扫描完成
↓
恢复业务线程
```

这就是 `Stop-The-World`。

---

### 15.2 并发 GC

现代 GC 会尝试让：

```text
GC Thread
+
Application Thread
```

同时运行，以减少长时间停顿。

但这样就产生新的问题：

> GC 扫描期间，业务线程还在修改引用怎么办？

这就需要写屏障等机制帮助 GC 记录引用变化。

---

## 16. 三色标记

为了理解并发标记，学习了三色标记模型：

- 白色：还没访问。
- 灰色：对象已经发现，但它引用的对象还没全部扫描。
- 黑色：对象自身及其引用都已扫描完成。

例如：

```text
Root → A → B → C
```

可以经历：

```text
A 灰，B 白，C 白
↓
A 黑，B 灰，C 白
↓
A 黑，B 黑，C 灰
↓
全部黑
```

最终仍为白色的对象可视为不可达对象。

---

## 17. 垃圾回收的三个经典算法

### 17.1 标记-清除

```text
[A][垃圾][B][垃圾][C]
```

清除后：

```text
[A][空][B][空][C]
```

优点：

- 思路简单。

缺点：

- 会产生内存碎片。

---

### 17.2 复制算法

把内存分成两个区域，平时使用其中一边，GC 时把存活对象复制到另一边。

```text
区域1：
[A][垃圾][B][垃圾][C]

GC 后区域2：
[A][B][C]
```

优点：

- 没有碎片。
- 如果存活对象很少，回收很高效。

缺点：

- 需要额外空间。
- 如果大量对象都存活，复制成本高。

因此适合：

> 大量对象很快死亡的区域。

---

### 17.3 标记-整理

```text
原来：
[A][垃圾][B][垃圾][C]

整理：
[A][B][C][空][空]
```

优点：

- 减少碎片。
- 不需要简单浪费一半空间。

缺点：

- 需要移动对象。
- 对象移动后引用也要更新。

---

## 18. 分代垃圾回收

JVM 利用了一个重要观察：

> 大多数 Java 对象生命周期很短，少量对象会长期存活。

因此堆可以按对象“年龄”划分：

```text
Heap
├── Young Generation
└── Old Generation
```

年轻代进一步可以理解为：

```text
Young Generation
├── Eden
├── Survivor 0
└── Survivor 1
```

---

### 18.1 新生对象

大量新对象首先进入 Eden：

```java
new User();
new Order();
new ArrayList<>();
```

Eden 快满时，会触发年轻代回收，即本次学习中提到的 `Young GC / Minor GC`。

---

### 18.2 Survivor

如果某对象经过 Young GC 后仍然存活，会进入 Survivor。

例如：

```text
Eden
[A][B][C][D][E]

GC 后只剩：
[B][E]
```

可以把存活对象复制到 Survivor，然后清空原区域。

S0 / S1 会轮流作为 From / To：

```text
GC 前：
Eden + S0 有对象
S1 空

GC 后：
Eden + S0 清空
S1 保存活对象
```

下一次则反过来。

---

### 18.3 对象年龄与晋升

可以把新对象理解成：

```text
age = 0
```

经历一次 Young GC 仍存活：

```text
age = 1
```

继续存活：

```text
age = 2
age = 3
...
```

最终可能晋升到 Old Generation。

本次学习中提到：

- 经典情况下常提到默认最大年龄大约 15。
- 但不能理解为“所有对象一定活满 15 次 GC 才晋升”。
- Survivor 装不下等情况可能导致提前晋升。

因此：

> 年龄是晋升依据之一，不是唯一依据。

---

### 18.4 大对象

本次只提到：

> 特别大的对象有时不会完整经历 Eden → Survivor → Old 的普通路径，可能直接进入老年代或特殊区域，具体取决于垃圾收集器和配置。

没有继续深入。

---

## 19. Young GC、Major GC 与 Full GC

### Young GC

主要处理年轻代：

```text
Eden + Survivor
```

特点：

- 相对频繁。
- 通常比大范围 GC 更快。
- 很多临时对象在这里被回收。

---

### Major GC

本次明确指出：

> `Major GC` 不是一个特别严格统一的 JVM 规范术语。

很多资料用它表示老年代 GC，但不同垃圾收集器、工具中的含义可能不同。

因此看到 `Major GC` 时需要结合上下文理解。

---

### Full GC

本次采用的粗略理解：

> 对整个 JVM 堆乃至部分其他相关内存区域进行一次大规模回收。

相比 Young GC，Full GC 涉及更大的对象范围，往往也会伴随更明显的 STW。

线上真正需要担心的是：

> 频繁 Full GC + 每次暂停时间很长。

偶发 Full GC 不一定意味着事故。

---

### 本次提到的典型触发方向

只保留会话中讨论过的：

- 老年代空间紧张。
- Metaspace 紧张。
- `System.gc()`。
- 某些收集器出现晋升失败等情况。

没有继续深入具体收集器下的详细触发规则。

---

## 20. Serial、Parallel 与 G1

本次没有把垃圾收集器理解成简单的“前后替代关系”，而是理解为不同目标下的权衡。

两个核心指标：

- 吞吐量：程序真正执行业务的时间占比。
- 停顿时间：一次 GC 让业务线程停多久。

---

### 20.1 Serial GC

```text
业务线程运行
↓
STW
↓
单线程 GC
↓
恢复
```

特点：

- 实现简单。
- 单线程回收。
- 小堆、小程序比较适合。
- 大堆下停顿会更明显。

---

### 20.2 Parallel GC

```text
STW
↓
多个 GC 线程并行回收
↓
恢复
```

相比 Serial：

> GC 本身并行化。

目标偏向：

> 高吞吐量。

---

### 20.3 G1

G1 将堆切成很多大小相同的 Region：

```text
[R][R][R][R]
[R][R][R][R]
[R][R][R][R]
```

这些 Region 可以承担不同角色：

```text
Eden
Survivor
Old
Free
```

G1 仍然保留分代思想，但物理上不要求年轻代和老年代连续：

```text
[Eden][Old ][Eden][Surv]
[Old ][Old ][Eden][Free]
```

因此：

- 逻辑上仍然有 Young / Old。
- 物理上由许多离散 Region 组成。
- Region 的角色可以动态变化。

---

### 20.4 Garbage First 的直觉

假设：

```text
R1：90% 垃圾
R2：10% 垃圾
R3：70% 垃圾
R4：5% 垃圾
```

如果回收时间有限，优先处理 R1、R3 更划算。

因此本次采用的理解是：

> G1 会关注不同 Region 的回收收益，并优先处理更“划算”的区域。

---

## 21. Card Table、Remembered Set 与跨代引用

一个重要问题：

> 如果 Old 对象引用了 Young 对象，Young GC 为什么不用扫描整个老年代？

例如：

```text
Old Object
    |
    v
Young Object
```

如果 Young GC 完全忽略 Old，就可能误回收这个 Young 对象。

---

### 21.1 Card Table

可以把老年代切成很多小块：

```text
[Card][Card][Card][Card]
```

如果发生：

```java
oldObj.child = youngObj;
```

JVM 会把对应 Card 标成 `dirty`。

Young GC 时，不必扫描整个 Old，只重点检查这些 dirty Card。

核心思想：

> 平时记录跨代引用可能出现的位置，GC 时缩小扫描范围。

---

### 21.2 Remembered Set

本次采用的直观理解：

> 某个 Region 用来记录“哪些其他区域可能引用了我”。

例如：

```text
Old Region A
   ↓
Young Region B
```

B 相关的 Remembered Set 可以帮助 GC 知道：

```text
A 的某些位置可能引用了 B
```

---

## 22. 写屏障与内存屏障

### 22.1 Write Barrier

如果业务线程执行：

```java
oldObj.child = youngObj;
```

JVM 除了完成普通赋值，还可能需要顺便记录：

> 这里的引用关系发生了变化。

可以粗略理解为：

```java
oldObj.child = youngObj;
// 概念上额外：
markCardDirty(oldObj);
```

这就是本次学习中的 `Write Barrier`。

它属于 GC 机制。

核心权衡：

```text
平时引用变化时多维护一点信息
↓
GC 时少扫描大量内存
```

---

### 22.2 Memory Barrier

`Memory Barrier / Memory Fence` 属于并发和 CPU 内存模型，用于限制重排、保证一定的可见性和顺序。

因此：

```text
Write Barrier
→ GC

Memory Barrier
→ 并发 / CPU 内存顺序
```

名字类似，但不是同一个概念。

---

## 23. Java GC 的资源成本与取舍

学习过程中出现过一个直观感受：

> Java 的垃圾回收机制看起来需要不少额外资源，内存利用率似乎也没有手动内存管理那么紧。

本次得到的理解是：

Java/JVM 的 GC 确实是在用：

- 额外 CPU
- 额外内存余量
- GC 元数据
- 回收过程

换取自动内存管理。

例如堆不能简单理解为：

```text
活对象用了 4 GB
→ JVM 只要给 4 GB 就够
```

因为 GC 还需要复制、晋升、整理等工作空间。

与手动管理相比：

```text
C/C++
→ 开发者自己管理生命周期
→ 可以把内存抠得更紧
→ 但容易出现泄漏、悬空指针、UAF

Java/JVM
→ GC 自动管理
→ 多消耗一些 CPU / 内存
→ 换取自动内存管理和更高的内存安全性
```

因此不能简单得出“Java 不行”，而应该理解成不同设计取舍。

---

## 24. 为什么 `new` 通常没有想象中那么重

虽然 GC 很复杂，但对象分配本身通常可以很快。

### 24.1 指针碰撞

Eden 内存规整时：

```text
[ 已使用 ][        空闲        ]
           ↑
          top
```

分配一个对象可以近似理解为：

```text
oldTop = top
top += objectSize
return oldTop
```

本质上只是移动一个指针。

---

### 24.2 TLAB

多个线程同时 `new` 对象时，如果都操作同一个分配指针会有竞争。

JVM 可以给每个线程预先划一小块自己的 Eden 区域：

> TLAB：Thread Local Allocation Buffer

```text
Eden

[TLAB A][TLAB B][TLAB C][...]
```

于是：

```text
Thread A → 自己的 TLAB
Thread B → 自己的 TLAB
```

线程在自己的 TLAB 中分配对象时，通常只需移动自己的指针，不需要频繁和其他线程竞争。

因此可以把 JVM 的一种典型思路理解为：

> 分配快，回收批量做。

---

## 25. 逃逸分析与标量替换：仅建立概念

本次只简单提到，还没有继续深入。

例如：

```java
void test() {
    Point p = new Point(1, 2);
    int x = p.x + p.y;
}
```

如果 JIT 判断 `p` 不会逃出这个方法，理论上可以继续优化。

可能做类似：

> 标量替换（Scalar Replacement）

将对象拆成普通值来处理，而不一定真的保留一个完整的堆对象。

因此：

> 源码里出现 `new`，不等于运行时一定以最朴素方式在堆里完整创建对象。

这一部分在本轮学习中主动停止，没有继续深入。

---

## 26. 类加载机制

GC 部分学习到一定深度后，学习方向转到 JVM 的另一条主干：类加载。

整体过程：

```text
Loading
↓
Verification
↓
Preparation
↓
Resolution
↓
Initialization
```

其中：

```text
Verification + Preparation + Resolution
```

合称：

> Linking

因此也可以写成：

```text
Loading
↓
Linking
↓
Initialization
```

---

### 27. Loading：加载

作用：

> 找到 `.class` 字节数据，并让 JVM 能够管理这个类。

例如：

```text
User.class
↓
ClassLoader
↓
JVM 内部的 User 类信息
```

Java 层还会对应：

```java
Class<User>
```

例如：

```java
Class<?> clazz = User.class;
```

这也和反射联系起来：

> 反射能够查询类的字段和方法，是因为 JVM 已经加载并保存了类元数据。

---

### 28. Verification：验证

JVM 不会完全信任 `.class` 文件。

需要验证字节码是否符合要求，例如不能出现：

```text
本来应该返回 int
却返回 Object 引用
```

或者 class 文件结构损坏。

核心目的：

> 避免非法或损坏字节码破坏 JVM 的执行环境。

---

### 29. Preparation：准备

例如：

```java
class User {
    static int count = 10;
}
```

准备阶段先为静态变量分配空间，并赋默认零值：

```text
count = 0
```

此时通常还不是 10。

---

### 30. Resolution：解析

`.class` 中很多内容最初是符号引用，例如：

```text
User.work:()V
```

解析阶段会把这类符号引用逐步变成 JVM 可以直接定位的引用。

可以理解成：

```text
“调用 User.work”
↓
找到真正对应的方法
```

---

### 31. Initialization：初始化

初始化阶段才真正执行类初始化逻辑，例如：

```java
class User {
    static int count = 10;

    static {
        System.out.println("init");
    }
}
```

会执行：

```text
count = 10
```

以及：

```java
static { ... }
```

#### 易错点：Preparation 和 Initialization

不要混淆：

```text
Preparation
→ count = 0

Initialization
→ count = 10
→ 执行 static {}
```

---

### 32. 哪些情况会触发类初始化

本次学习中讨论了以下情况。

#### 32.1 `new`

```java
User user = new User();
```

如果 `User` 尚未初始化，则先初始化 `User`，再创建对象。

---

#### 32.2 访问普通静态字段

```java
System.out.println(User.count);
```

如果 `count` 是普通静态字段，通常会触发 `User` 初始化。

---

#### 32.3 调用静态方法

```java
User.login();
```

如果 `User` 尚未初始化，会先初始化。

---

#### 32.4 `Class.forName()`

```java
Class.forName("com.example.User");
```

默认情况下，不只是加载，还会进行初始化。

如果类中有：

```java
static {
    System.out.println("init");
}
```

则可能在 `Class.forName()` 时执行。

---

### 33. 不一定触发子类初始化的情况

例如：

```java
class Parent {
    static int value = 10;
}

class Child extends Parent {
}
```

执行：

```java
System.out.println(Child.value);
```

由于 `value` 实际定义在 `Parent`，本次学习中得到的结论是：

> 通常只会初始化 Parent，而不一定初始化 Child。

---

### 34. 编译期常量

例如：

```java
class Config {
    static final int MAX = 100;

    static {
        System.out.println("Config init");
    }
}
```

执行：

```java
System.out.println(Config.MAX);
```

本次学习中提到：

> 这种编译期常量可能在编译阶段直接写入调用方字节码，因此可能不触发 `Config` 初始化。

所以：

```text
static final 编译期常量
```

和普通 `static` 字段在类初始化行为上可能不同。

---

### 35. 父类和子类的初始化顺序

如果：

```java
class Child extends Parent
```

第一次：

```java
new Child();
```

初始化顺序通常是：

```text
Parent 初始化
↓
Child 初始化
```

---

### 36. JVM 类加载与 Spring Bean 生命周期不是一回事

例如：

```java
@Component
class UserService {
}
```

存在两个不同层次：

```text
JVM
↓
加载 UserService 类

Spring
↓
创建和管理 UserService Bean
```

可以理解为：

```text
ClassLoader
↓
UserService 类进入 JVM
↓
Spring
↓
通过 new / 反射等方式创建 UserService 实例
↓
Bean 生命周期
```

因此：

> JVM 类加载负责“类可以被 Java 运行时使用”，Spring Bean 生命周期负责“对象怎么被 Spring 创建和管理”。

---

## 37. 三类主要 ClassLoader

当前学习中介绍了：

```text
Bootstrap ClassLoader
        ↓
Platform ClassLoader
        ↓
Application ClassLoader
```

旧资料中常见：

```text
Bootstrap
Extension
Application
```

Java 9 之后，`Extension ClassLoader` 基本被 `Platform ClassLoader` 取代。

---

### 38. Bootstrap ClassLoader

负责加载 Java 的核心类，例如本次举例：

```text
java.lang.String
java.lang.Object
java.util.*
```

它属于 JVM 很底层的一部分。

---

### 39. Platform ClassLoader

负责加载 JDK 平台相关模块中的类。

本轮没有进一步深入具体模块范围。

---

### 40. Application ClassLoader

最贴近普通应用。

项目里的：

```text
target/classes
各种依赖 jar
```

通常主要由 Application ClassLoader 加载。

例如：

```text
UserService
AuthController
AuthService
Spring 相关依赖
MySQL Driver
Redis 相关类
```

都需要类加载器加载进 JVM。

---

## 41. 双亲委派

#### 41.1 核心规则

双亲委派不是“有两个父亲”。

这里的“parent”指类加载器的父加载器。

默认思路：

> 一个 ClassLoader 收到加载请求时，先委托给父加载器尝试；父加载器找不到后，自己才加载。

例如加载：

```text
java.lang.String
```

可以理解成：

```text
Application
↓ 委托
Platform
↓ 委托
Bootstrap
↓
Bootstrap 能加载 String
↓
直接返回
```

而加载：

```text
com.example.User
```

可以理解成：

```text
Application
↓
Platform 找不到
↓
Bootstrap 找不到
↓
Application 自己加载
```

#### 易错点：双亲委派不是“父类加载器加载所有类”

正确理解：

> 父加载器有优先尝试权，但父加载器找不到时，子加载器仍然可以自己加载。

---

### 42. 为什么需要双亲委派

重要目的之一：

> 避免核心 Java 类被随意替换。

例如自己写：

```java
package java.lang;

public class String {
}
```

如果应用类加载器可以直接优先加载它，就可能替换真正的 JDK `String`。

双亲委派下：

```text
加载 java.lang.String
↓
优先交给 Bootstrap
↓
Bootstrap 找到真正的 String
↓
返回
```

应用自己写的假 `String` 就没有机会覆盖核心类。

因此双亲委派带来的作用包括：

- 提高核心类的一致性。
- 防止核心 API 被轻易替换。
- 减少基础类被不同加载器重复加载的问题。

---

### 43. 类身份与 ClassLoader

JVM 判断两个类是不是同一个类，不只看类名，还和加载它的 ClassLoader 有关。

本次采用的粗略理解：

```text
类身份
≈ 类全限定名 + ClassLoader
```

因此：

```text
com.example.User
```

即使名字完全相同，如果由两个不同的 ClassLoader 分别加载，JVM 可能把它们视为不同的类。

这可以导致一种看起来很奇怪的情况：

> 类名一样，却发生 `ClassCastException`。

---

## 44. 为什么有些系统会打破默认双亲委派

双亲委派解决的是：

> 核心类不要被替换。

但有些系统需要：

> 同一个类名 / 同一依赖的不同版本可以同时存在。

例如：

```text
应用 A → Logger v1
应用 B → Logger v2
```

如果所有类都完全交给同一个父加载器，就难以实现版本隔离。

---

### 45. Tomcat 的类加载隔离

传统 Tomcat 可以在同一个 JVM 中承载多个 Web 应用：

```text
Tomcat JVM

WebApp1
└── ClassLoader1

WebApp2
└── ClassLoader2

WebApp3
└── ClassLoader3
```

不同应用可能依赖：

```text
App1 → Spring 5
App2 → Spring 6
```

因此 Tomcat 需要更复杂的类加载策略，给不同 WebApp 提供隔离。

本次采用的直观理解是：

> 某些场景下 WebApp 会优先尝试自己的 ClassLoader，再向父加载器委派。

这属于对默认双亲委派策略的调整。

---

### 46. SPI 与线程上下文类加载器

SPI 场景中的问题：

接口可能由 JDK 提供：

```text
java.sql.Driver
```

但实现来自用户依赖：

```text
MySQL Driver
PostgreSQL Driver
```

父加载器可以看到 JDK 接口，却不一定能直接看到下层应用 jar 中的实现。

因此 SPI 场景会用到：

> Thread Context ClassLoader

相关 API：

```java
Thread.currentThread()
      .getContextClassLoader()
```

本次理解：

> JDK / 上层代码可以借用当前应用的 ClassLoader 去加载第三方实现。

---

## 47. 当前学习阶段的重点易错点汇总

### 47.1 `count` 局部变量不是方法区内容

```java
void work() {
    int count = 10;
}
```

- `count` → 当前线程栈帧。
- 不要因为右边是常量 `10`，就把变量本身和常量池混在一起。

---

### 47.2 对象不可达不等于立即被释放

```text
失去所有 Root 可达路径
↓
对象变为不可达
↓
等待未来 GC
```

不是：

```text
引用消失
↓
对象瞬间删除
```

---

### 47.3 被其他对象引用，不等于程序还能访问到

循环引用：

```text
A → B
↑   ↓
└───┘
```

如果外界没有 Root 能到达 A/B，它们仍然是垃圾。

---

### 47.4 STW 不能直接解决引用计数的循环问题

STW 只能暂时冻结引用关系。

它不能让：

```text
A 引用 B
B 引用 A
```

自动变成：

```text
A count = 0
B count = 0
```

---

### 47.5 Java 有 GC 仍然会内存泄漏

原因可以是：

> 已经业务无用的对象仍被长期引用。

尤其是静态集合：

```java
static List<Object> cache = new ArrayList<>();
```

如果不断加而不删除，这些对象对 GC 来说始终可达。

---

### 47.6 方法区与对象本身不要混淆

```text
“User 有 age 字段”
→ 类结构信息

“某个 User.age = 20”
→ 具体对象状态
```

---

### 47.7 Preparation 和 Initialization 不要混淆

例如：

```java
static int count = 10;
```

本次学习采用：

```text
Preparation
→ count = 0

Initialization
→ count = 10
```

---

### 47.8 JVM 类加载与 Spring Bean 创建不是同一层

```text
ClassLoader
→ 让类进入 JVM

Spring
→ 创建和管理 Bean 对象
```

---

### 47.9 Write Barrier 与 Memory Barrier 不是一回事

```text
Write Barrier
→ GC 引用变化记录

Memory Barrier
→ 并发 / CPU 内存顺序
```

---

### 47.10 双亲委派不是“父加载器全包”

真正的默认思路：

```text
子加载器收到请求
↓
先问父加载器
↓
父加载器找不到
↓
子加载器自己加载
```

---

## 48. 当前 JVM 学习进度

本轮已经覆盖：

```text
JVM 总体运行模型
↓
运行时数据区
↓
栈帧
↓
对象创建
↓
GC Roots / 可达性分析
↓
经典回收算法
↓
分代 GC
↓
Young / Full GC
↓
Serial / Parallel / G1
↓
Region / Card Table / RSet / Write Barrier
↓
TLAB
↓
类加载流程
↓
ClassLoader
↓
双亲委派
↓
Tomcat / SPI 的特殊类加载场景
```

当前主动没有继续深入的内容：

```text
逃逸分析细节
G1 更底层实现
ZGC / Shenandoah
GC 日志与调优
Safepoint
字节码文件结构细节
JIT 深入
```

下一阶段原计划进入：

```text
.class / 字节码执行
↓
解释器
↓
JIT
↓
热点代码
```

但在继续之前，当前最需要再次复习的是：

> 三类主要 ClassLoader 的职责，以及双亲委派中“先委托父加载器，父加载器失败后子加载器自己加载”的实际流程。
