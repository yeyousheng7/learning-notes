# MySQL EXPLAIN 与索引设计学习笔记

## 1. EXPLAIN 的定位

`EXPLAIN` 可以用来查看 SQL 的执行计划。

本轮学习的目标不是深入优化器内部，而是先建立一套基础分析方法：

1. SQL 最终用了哪个索引？
2. 通过什么方式访问数据？
3. 预计要检查多少行？
4. 是否需要回表？
5. 是否发生额外过滤、排序或临时处理？
6. 联合索引的字段顺序是否真正符合查询模式？

本轮重点关注的字段：

```text
type
possible_keys
key
rows
Extra
```

后续还接触到了：

```text
key_len
```

---

## 2. EXPLAIN 的核心字段

### 2.1 possible_keys

`possible_keys` 表示：

> 优化器认为“理论上可能可以使用”的索引。

例如：

```sql
SELECT *
FROM user
WHERE id = 100;
```

如果 `id` 是主键：

```text
possible_keys = PRIMARY
```

但要注意：

> `possible_keys` 只是候选索引，不代表最终一定使用。

例如可能出现：

```text
possible_keys = idx_age
key = NULL
```

表示 `idx_age` 理论上可能参与查询，但优化器最后没有选择它。

---

### 2.2 key

`key` 表示：

> 实际选择使用的索引。

例如：

```text
key = PRIMARY
```

表示实际使用了主键索引。

如果：

```text
key = idx_age
```

表示实际使用了名为 `idx_age` 的索引。

如果：

```text
key = NULL
```

表示最终没有使用索引进行该访问。

---

### 2.3 rows

`rows` 表示：

> 优化器预计需要检查多少行。

它不是：

> SQL 最终一定返回多少行。

例如：

```sql
SELECT *
FROM user
WHERE age > 20;
```

最终可能只返回 100 行，但执行计划仍可能估计：

```text
rows = 50000
```

因为优化器预计需要检查大量候选记录。

#### 易错点：把 rows 当成条件值数量

例如：

```sql
WHERE age BETWEEN 20 AND 30
```

不能因为 `20~30` 只有若干个年龄值，就写：

```text
rows = 10
```

因为每个年龄可能对应很多行。

例如：

```text
age = 20 → 3000 人
age = 21 → 2500 人
...
```

所以 `rows` 和“范围里包含多少个值”不是一回事。

---

### 2.4 Extra

`Extra` 用来补充执行过程中的额外信息。

本轮出现的主要值有：

```text
Using index
Using where
Using index condition
Using filesort
Using temporary
```

其中：

```text
Using index
```

和：

```text
type = index
```

不是一回事。

这也是本轮非常容易混淆的地方之一。

---

## 3. type：数据是怎么被访问的

本轮重点学习了：

```text
const
ref
range
index
ALL
```

可以先用下面的方式建立直觉：

```text
const  → 唯一索引等值定位，最多一行
ref    → 普通索引等值查询，可能很多行
range  → 索引范围扫描
index  → 扫完整个索引
ALL    → 扫完整张表
```

粗略趋势可以记成：

```text
const > ref > range > index > ALL
```

但这只是很粗略的通常趋势：

> 不能只看 `type` 就断言 SQL 一定快或慢。

---

### 3.1 const

假设：

```sql
CREATE TABLE user (
    id BIGINT PRIMARY KEY
);
```

查询：

```sql
SELECT *
FROM user
WHERE id = 100;
```

因为 `id` 是主键，一个值最多对应一行，所以：

```text
type = const
key = PRIMARY
rows ≈ 1
```

可以先把 `const` 理解为：

> 通过主键或唯一索引的等值条件，最多确定一行。

---

### 3.2 ref

假设：

```sql
INDEX idx_username(username)
```

查询：

```sql
SELECT *
FROM user
WHERE username = 'alice';
```

因为 `idx_username` 是普通索引：

```text
type = ref
key = idx_username
```

它可能命中：

```text
alice -> row 1
alice -> row 2
alice -> row 3
...
```

所以：

> `ref` 也完全可能返回或检查一批数据。

#### 易错点：把 ref 理解成“只能找到一行”

错误理解：

```text
ref → 只找一行
```

正确理解：

```text
ref → 普通索引上的等值查询
```

例如：

```sql
WHERE age = 20
```

即使匹配 5000 行，也仍然可能是：

```text
type = ref
```

因为关键在于“怎么找”，而不是“最终有多少行”。

---

### 3.3 range

`range` 的核心是：

> 通过索引确定一个范围，然后扫描这个范围。

最典型的条件：

```sql
WHERE age > 20
WHERE age >= 20
WHERE age < 30
WHERE age BETWEEN 20 AND 30
```

常见执行计划：

```text
type = range
key = idx_age
```

`IN` 也可能表现为 `range`。

#### ref 与 range 的关键区别

```sql
WHERE age = 20
```

通常：

```text
type = ref
```

而：

```sql
WHERE age > 20
```

通常：

```text
type = range
```

所以：

```text
ref   → 找“等于某个确定值”的一批记录
range → 扫描索引上的一段范围
```

#### 易错点：把 range 理解为“返回很多行”

`ref` 和 `range` 都可能匹配很多行。

区别不在返回数量，而在索引访问方式。

---

### 3.4 ALL

假设：

```sql
SELECT *
FROM user
WHERE nickname = 'Tom';
```

而 `nickname` 没有索引。

MySQL 没法直接定位，只能扫描整张表并判断：

```text
type = ALL
key = NULL
rows = 很多
```

所以：

> `ALL` 表示全表扫描。

#### 易错点：无索引等值查询不是 range

曾出现误解：

```sql
WHERE nickname = 'Tom'
```

虽然是一个条件，但如果 `nickname` 没有可用索引，并不是：

```text
type = range
```

而更可能是：

```text
type = ALL
```

因为 `range` 的前提是存在可以用于范围扫描的索引。

---

### 3.5 index

`type = index` 表示：

> 扫描整个索引。

例如：

```text
ALL   = 扫整张表
index = 扫整个索引
```

`index` 通常可能比 `ALL` 好一些，因为索引往往比完整数据行更小，但本质仍然属于“全扫描”。

#### 三个 index 概念不要混淆

例如：

```text
type = ref
key = idx_age
Extra = Using index
```

三者含义完全不同：

| 位置 | 示例 | 含义 |
|---|---|---|
| `key` | `idx_age` | 实际用了哪个索引 |
| `type` | `index` | 扫整个索引 |
| `Extra` | `Using index` | 查询被索引覆盖，不需要回表 |

---

## 4. InnoDB 二级索引、主键与回表

假设：

```sql
CREATE TABLE user (
    id BIGINT PRIMARY KEY,
    username VARCHAR(50),
    age INT,
    INDEX idx_age(age)
);
```

虽然索引定义看起来只有：

```sql
INDEX idx_age(age)
```

但本轮使用的理解模型是：

> InnoDB 的二级索引叶子节点可以粗略理解成保存了索引列和主键。

所以：

```text
idx_age
```

可以粗略理解成：

```text
(age, id)
```

例如：

```text
id   username   age
101  Alice      20
102  Bob        18
108  Carol      20
```

`idx_age` 可以粗略想象成：

```text
(18, 102)
(20, 101)
(20, 108)
```

---

### 4.1 为什么二级索引需要主键 id

假设：

```sql
SELECT *
FROM user
WHERE age = 20;
```

先通过：

```text
idx_age
```

找到：

```text
age = 20 → id = 101
age = 20 → id = 108
```

但 `idx_age` 中没有完整的 `username` 等字段。

于是需要：

```text
idx_age
   ↓
得到主键 id
   ↓
PRIMARY
   ↓
找到完整数据行
```

这个过程叫：

> 回表。

---

### 4.2 覆盖索引

如果查询是：

```sql
SELECT id
FROM user
WHERE age = 20;
```

需要的字段只有：

```text
条件：age
结果：id
```

而 `idx_age` 已经可以粗略理解为：

```text
(age, id)
```

所以可以直接：

```text
idx_age
↓
找到 age=20
↓
直接拿 id
↓
结束
```

不需要访问主键索引中的完整数据行。

这就是：

> 覆盖索引。

此时 `Extra` 可能出现：

```text
Using index
```

---

### 4.3 易错点：SELECT id 不是“改用主键索引”

曾出现的理解：

> 因为 `id` 是主键，所以 `SELECT id` 可能改用了主键索引。

正确理解：

> 仍然可以使用 `idx_age`，只是 `idx_age` 自己已经保存了主键 `id`，因此不需要再访问 `PRIMARY`。

例如：

```text
key = idx_age
Extra = Using index
```

表示：

- 仍然使用 `idx_age`
- 查询被 `idx_age` 覆盖
- 没有因为 `SELECT id` 就自动改成主键索引

---

### 4.4 如何判断是否回表

核心问题是：

> 当前使用的二级索引是否已经包含查询需要的所有字段？

例如：

```sql
INDEX idx_age(age)
```

粗略看成：

```text
(age, id)
```

则：

```sql
SELECT id
FROM user
WHERE age = 20;
```

可以覆盖。

```sql
SELECT age
FROM user
WHERE age = 20;
```

可以覆盖。

```sql
SELECT id, age
FROM user
WHERE age = 20;
```

也可以覆盖。

但是：

```sql
SELECT username
FROM user
WHERE age = 20;
```

`username` 不在 `idx_age` 中，因此需要回表。

---

## 5. Using index、Using where 与 Using index condition

### 5.1 Using index

`Extra = Using index` 表示：

> 查询所需数据可以直接从索引中取得，不需要回表。

例如：

```sql
SELECT id, age
FROM user
WHERE age BETWEEN 20 AND 30;
```

如果：

```sql
INDEX idx_age(age)
```

则索引可以粗略理解为：

```text
(age, id)
```

查询条件和结果字段都在索引中，因此可能：

```text
type = range
key = idx_age
Extra = Using index
```

有时也可能同时看到：

```text
Using where; Using index
```

两者不冲突。

---

### 5.2 Using where

`Using where` 更准确的理解是：

> MySQL 拿到候选记录后，还需要继续应用 `WHERE` 条件进行过滤。

#### 易错点：Using where 不是回表

错误理解：

> `Using where` 一般是因为回表。

正确理解：

> `Using where` 和回表没有直接对应关系。

例如：

```sql
SELECT *
FROM user
WHERE nickname = 'Tom';
```

如果 `nickname` 无索引：

```text
type = ALL
key = NULL
Extra = Using where
```

这里是全表扫描后逐行判断，与二级索引回表无关。

甚至：

```text
Using where; Using index
```

也可能同时出现，表示：

- 还需要 `WHERE` 过滤
- 但查询被索引覆盖，不回表

因此：

> 单独看到 `Using where` 不需要紧张。

更值得警惕的是：

```text
type = ALL
rows = 1000000
Extra = Using where
```

这意味着扫描大量行再过滤。

而：

```text
type = ref
rows = 20
Extra = Using where
```

通常问题就小很多。

分析时应该把：

```text
type + key + rows + Extra
```

一起看，而不是单独盯着 `Using where`。

---

### 5.3 Using index condition：ICP

假设联合索引：

```sql
INDEX idx_age_username(age, username)
```

查询：

```sql
SELECT *
FROM user
WHERE age > 20
  AND username = 'alice';
```

因为：

```text
age
```

在最左边，并且是范围条件，所以它可以确定索引扫描范围。

但：

```text
username = 'alice'
```

无法继续把整个 B+Tree 扫描范围缩成一个全局连续的小范围。

#### 没有 ICP 时的粗略过程

```text
根据 age > 20 扫描索引
↓
拿到一条索引记录
↓
根据主键回表
↓
读取完整行
↓
再判断 username 是否等于 alice
```

这样可能产生很多无效回表。

#### ICP 的思路

因为 `username` 本身就在：

```text
idx_age_username
```

里，所以可以先在索引层判断：

```text
username = 'alice'
```

执行过程变成：

```text
扫描 idx_age_username
↓
先判断 username
↓
不满足 → 直接丢掉，不回表
满足   → 再回表
```

这就是：

> Index Condition Pushdown（ICP）。

其主要价值在本轮中理解为：

> 减少回表次数。

#### Using index 与 Using index condition 的区别

```text
Using index
→ 覆盖索引
→ 根本不需要回表
```

```text
Using index condition
→ ICP
→ 仍然可能需要回表
→ 但先在索引层过滤，减少无效回表
```

---

## 6. 索引列上的表达式与隐式类型转换

### 6.1 对索引列做计算

假设：

```sql
INDEX idx_age(age)
```

查询：

```sql
SELECT *
FROM user
WHERE age + 1 = 21;
```

虽然人可以直接看出：

```text
age + 1 = 21
⇔
age = 20
```

但本轮得到的结论是：

> 一般不能指望 MySQL 自动做这种代数改写，然后继续利用普通 `idx_age(age)`。

所以常见结果更接近：

```text
possible_keys = NULL
key = NULL
type = ALL
```

问题不是数据库“不会算 `age + 1`”，而是：

> 普通 B+Tree 索引按 `age` 的原始值组织，条件却作用在 `age + 1` 上。

所以应该高度警惕：

```sql
WHERE age + 1 = 21
WHERE YEAR(create_time) = 2026
WHERE LOWER(username) = 'alice'
```

会话中给出的更适合索引的改写示例包括：

```sql
WHERE age = 20
```

以及：

```sql
WHERE create_time >= '2026-01-01'
  AND create_time <  '2027-01-01'
```

本轮还提到：

> 如果专门为某个表达式建立可以利用的索引结构，则属于另外的情况；不能把它和普通 `idx_age(age)` 混为一谈。

---

### 6.2 隐式类型转换不是“必然索引失效”

假设：

```text
age INT
```

且：

```sql
INDEX idx_age(age)
```

查询：

```sql
WHERE age = '20'
```

本轮结论是：

> `idx_age` 很可能仍然可以使用。

因此不能机械记成：

```text
发生隐式类型转换
=
索引一定失效
```

关键要看：

> 索引列本身是否被迫进行转换。

---

### 6.3 VARCHAR 列与数字比较

假设：

```text
phone VARCHAR(20)
```

并且：

```sql
INDEX idx_phone(phone)
```

如果写：

```sql
WHERE phone = 13800138000
```

会话中强调这是一个危险写法，因为可能需要把字符串列转换成数值参与比较，导致无法利用字符串索引做快速查找。

更稳妥的写法：

```sql
WHERE phone = '13800138000'
```

因此实际开发里：

> SQL 参数类型最好和字段类型保持一致。

---

## 7. LIKE 与索引

假设：

```sql
INDEX idx_username(username)
```

### 7.1 前缀匹配

```sql
WHERE username LIKE 'ali%'
```

通常可以利用索引。

因为索引按字符串顺序组织，例如：

```text
adam
alice
alina
allen
bob
carol
```

以 `ali` 开头的数据在索引中可以形成连续范围。

因此可能：

```text
type = range
key = idx_username
```

---

### 7.2 前导通配符

```sql
WHERE username LIKE '%ali'
```

或：

```sql
WHERE username LIKE '%ali%'
```

通常不能利用普通 B+Tree 索引做快速定位。

原因是：

```text
ali
xxali
helloali
123ali
```

这些字符串按照从左到右排序时不会因为“结尾相同”而聚集成连续范围。

所以不能简单背：

```text
LIKE 会导致索引失效
```

正确理解应该是：

```text
'abc%'  → 通常可以利用索引范围
'%abc'  → 通常不行
'%abc%' → 通常不行
```

---

### 7.3 LIKE + 覆盖索引

例如：

```sql
SELECT id
FROM user
WHERE username LIKE 'ali%';
```

有：

```sql
INDEX idx_username(username)
```

二级索引可粗略理解成：

```text
(username, id)
```

所以：

```text
type = range
key = idx_username
Extra 可能有 Using index
```

原因是：

- `username LIKE 'ali%'` 可以做索引范围扫描
- 返回的 `id` 已经在二级索引中
- 不需要回表

---

## 8. 联合索引与最左前缀

假设：

```sql
INDEX idx_age_username(age, username)
```

它的顺序可以粗略理解为：

```text
先按 age 排序
age 相同时，再按 username 排序
```

例如：

```text
(18, alice)
(18, bob)
(20, adam)
(20, alice)
(20, tom)
(21, bob)
```

---

### 8.1 可以利用的查询

```sql
WHERE age = 20
```

可以利用：

```text
idx_age_username
```

因为从最左列开始。

```sql
WHERE age = 20
  AND username = 'alice'
```

也可以很好利用联合索引。

因为先通过：

```text
age = 20
```

确定一段，再在这一段内部继续通过：

```text
username = 'alice'
```

定位。

---

### 8.2 跳过最左列

```sql
WHERE username = 'alice'
```

通常不能很好利用：

```text
(age, username)
```

做快速定位。

原因是：

```text
(18, alice)
(20, alice)
(21, alice)
```

`alice` 散落在不同 `age` 区间中。

从 `username` 单独来看，这棵索引没有形成全局有序关系。

这就是本轮对：

> 最左前缀原则

的直观理解。

---

## 9. 联合索引遇到范围条件

假设：

```sql
INDEX idx_age_username(age, username)
```

查询：

```sql
WHERE age > 20
  AND username = 'alice'
```

本轮结论是：

> 如果讨论“用于缩小 B+Tree 搜索范围”，主要是 `age` 在起作用。

因为：

```text
age > 20
```

先确定了一个较大的索引范围。

这个范围中：

```text
(21, alice)
(21, bob)
(22, alice)
(22, tom)
...
```

`username='alice'` 并没有形成全局连续的一段。

所以 `username` 不能再像：

```sql
WHERE age = 20
  AND username = 'alice'
```

那样继续缩小整个索引定位范围。

---

### 9.1 易错点：范围条件之后的列“完全没用”

不能简单记成：

> 遇到范围后，后面的列完全失效。

更准确的是：

```text
age
→ 用来确定索引扫描范围

username
→ 仍可能在索引扫描过程中参与过滤
```

比如通过 ICP：

```text
Using index condition
```

先利用索引中已有的 `username` 过滤，再决定是否回表。

所以：

> “能不能用于缩小索引搜索范围”和“这个字段还能不能被利用”是两个不同问题。

---

## 10. key_len 的基本理解

本轮只建立了一个基础认识：

> `key_len` 大致反映实际使用了索引中的多长一段 key。

例如：

```sql
INDEX idx_age_username(age, username)
```

比较：

```sql
WHERE age = 20
```

与：

```sql
WHERE age = 20
  AND username = 'alice'
```

后者通常可能看到更长的 `key_len`，因为定位时利用到了更多联合索引列。

具体字节数受字段类型、是否允许 `NULL`、字符集等因素影响。

本轮没有要求记具体数字。

---

## 11. ORDER BY 与 Using filesort

### 11.1 Using filesort 的含义

`Using filesort` 表示：

> MySQL 不能直接利用现有索引顺序得到需要的结果，因此需要额外排序。

#### 易错点：filesort 不等于一定写磁盘文件

`filesort` 不是：

> 一定使用磁盘文件排序。

它表达的是：

> 需要额外的排序过程。

数据量小的时候，排序可能在内存中完成。

---

### 11.2 单列索引与排序

如果有：

```sql
INDEX idx_age(age)
```

查询：

```sql
SELECT *
FROM user
ORDER BY age;
```

MySQL 可能直接利用索引顺序。

而：

```sql
SELECT *
FROM user
ORDER BY username;
```

如果 `username` 没有合适索引，就可能：

```text
Using filesort
```

---

### 11.3 联合索引与排序

假设：

```sql
INDEX idx_age_username(age, username)
```

查询：

```sql
WHERE age = 20
ORDER BY username;
```

因为：

```text
age = 20
```

已经固定，所以 `age=20` 这一段内部天然按照 `username` 有序。

因此通常不需要：

```text
Using filesort
```

但是：

```sql
WHERE age > 20
ORDER BY username;
```

就不同。

索引可能类似：

```text
(21, alice)
(21, tom)
(22, bob)
(22, carol)
```

虽然每个 `age` 内部的 `username` 有序，但所有 `age > 20` 的记录放在一起时：

```text
alice
tom
bob
carol
```

并不是全局按照 `username` 排序。

因此通常仍然需要额外排序。

---

### 11.4 一个综合例子

```sql
SELECT id, username
FROM user
WHERE age = 20
ORDER BY username;
```

有：

```sql
INDEX idx_age_username(age, username)
```

可以分析为：

```text
age = 20
→ 普通索引等值查询
→ type = ref
```

```text
key = idx_age_username
```

二级索引粗略包含：

```text
(age, username, id)
```

所以：

- `SELECT id, username` 被覆盖
- 不需要回表
- `age=20` 这一段内部 `username` 已经有序
- 不需要 `Using filesort`

---

## 12. Using temporary

本轮建立的基础理解是：

> MySQL 需要额外创建临时结构来完成某些分组、去重、排序等处理时，`Extra` 可能出现 `Using temporary`。

例如讨论了：

```sql
SELECT age, COUNT(*)
FROM user
GROUP BY age;
```

如果：

```sql
INDEX idx_age(age)
```

MySQL 有机会利用索引顺序处理分组。

而：

```sql
SELECT username, COUNT(*)
FROM user
GROUP BY username;
```

如果 `username` 没有合适索引，则可能需要临时结构。

另外：

```sql
SELECT DISTINCT username
FROM user;
```

如果不能直接利用索引完成去重，也可能出现临时处理。

对 `Extra` 可以先建立这样的直觉：

```text
Using index
→ 通常是好事，覆盖索引

Using where
→ 很普通，本身不代表性能差

Using index condition
→ ICP，减少无效回表

Using filesort
→ 需要额外排序，需要关注

Using temporary
→ 需要额外临时结构，需要关注
```

但：

> 看到 `Using filesort` 或 `Using temporary` 不代表 SQL 一定很差。

仍然需要结合数据量等信息判断。

---

## 13. 一轮综合 EXPLAIN 判断方法

本轮练习后形成了一套比较实用的分析顺序。

面对一条 SQL，可以依次问：

```text
1. WHERE 能利用哪个索引？
2. 是等值(ref)还是范围(range)？
3. SELECT 的字段是否被当前索引覆盖？
   → 是否需要回表？
4. ORDER BY 是否符合索引已有顺序？
   → 是否需要 filesort？
5. rows 大概是少还是多？
6. Extra 是否说明还有过滤、ICP、排序或临时处理？
```

例如：

```sql
SELECT username
FROM user
WHERE age = 20;
```

有：

```sql
INDEX idx_age_username(age, username)
```

则：

```text
type = ref
key = idx_age_username
```

索引粗略包含：

```text
(age, username, id)
```

所以可以覆盖，不需要回表。

---

## 14. 联合索引设计：围绕查询模式，而不是追求万能索引

假设订单表：

```sql
CREATE TABLE orders (
    id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    status VARCHAR(20) NOT NULL,
    created_at DATETIME NOT NULL,
    amount DECIMAL(10, 2)
);
```

有三类查询：

```sql
-- A
SELECT *
FROM orders
WHERE user_id = 1001;
```

```sql
-- B
SELECT *
FROM orders
WHERE user_id = 1001
  AND status = 'PAID';
```

```sql
-- C
SELECT *
FROM orders
WHERE user_id = 1001
ORDER BY created_at DESC
LIMIT 20;
```

候选索引：

```sql
INDEX idx_user(user_id)

INDEX idx_user_status(user_id, status)

INDEX idx_user_created(user_id, created_at)
```

分别最适合：

```text
A → idx_user
B → idx_user_status
C → idx_user_created
```

但真正设计时，还要考虑索引之间是否冗余。

---

### 14.1 前缀索引冗余

如果已经有：

```sql
INDEX idx_user_status(user_id, status)
```

那么它本身就可以支持：

```sql
WHERE user_id = ?
```

因此单独的：

```sql
INDEX idx_user(user_id)
```

在这种查询能力上可能与联合索引重叠。

这是一种典型的：

> 前缀索引冗余。

---

### 14.2 一个联合索引不一定能解决所有查询

曾考虑：

```sql
INDEX (user_id, status, created_at)
```

希望同时解决：

```text
user_id
user_id + status
user_id + ORDER BY created_at
```

但对于：

```sql
WHERE user_id = 1001
ORDER BY created_at DESC
```

因为没有固定 `status`，索引内部只是：

```text
每个 status 分组内部 created_at 有序
```

并不是：

```text
user_id=1001 的所有记录全局按 created_at 有序
```

例如：

```text
1001, CANCELLED, 09-01
1001, CANCELLED, 09-08

1001, PAID,      09-03
1001, PAID,      09-09

1001, PENDING,   09-04
1001, PENDING,   09-07
```

因此 C 仍可能需要：

```text
Using filesort
```

所以：

> 不要为了“尽可能解决所有 SQL”就机械地造一个很长的联合索引。

---

### 14.3 `(user_id, status, created_at)` 适合什么查询

如果查询变成：

```sql
WHERE user_id = 1001
  AND status = 'PAID'
ORDER BY created_at DESC
LIMIT 20;
```

那么：

```text
user_id = 1001
→ 等值

status = PAID
→ 等值

created_at
→ 排序
```

因此：

```sql
INDEX (user_id, status, created_at)
```

就非常适合。

---

## 15. 联合索引字段顺序怎么定

### 15.1 “区分度高的字段一定放前面”并不准确

本轮明确指出：

> 联合索引字段顺序首先要看真实查询模式，而不是只看区分度。

例如：

```sql
WHERE user_id = ?
  AND status = ?
```

如果系统还经常：

```sql
WHERE user_id = ?
```

那么：

```sql
(user_id, status)
```

通常比：

```sql
(status, user_id)
```

更适合，因为它同时支持：

```text
user_id
user_id + status
```

即使 `user_id` 的区分度本来就更高，也不能只用“区分度”解释设计。

---

### 15.2 查询模式可能让低区分度字段放前面

如果系统经常：

```sql
WHERE status = ?
```

以及：

```sql
WHERE status = ?
  AND user_id = ?
```

那么：

```sql
(status, user_id)
```

反而可能更符合查询模式。

因此：

> 区分度是一个因素，但不是字段顺序的唯一决定因素。

---

### 15.3 等值条件通常放在范围条件前

查询：

```sql
WHERE status = 'PAID'
  AND created_at > '2026-09-01'
```

相比：

```text
(created_at, status)
```

本轮更倾向：

```text
(status, created_at)
```

原因：

```text
status = ...
→ 等值

created_at > ...
→ 范围
```

如果先放：

```text
created_at
```

一开始就进入范围扫描，后面的 `status` 通常不能再很好地继续缩小 B+Tree 搜索范围。

所以本轮形成的原则是：

```text
等值字段
→ 放前面

范围/排序字段
→ 通常放后面
```

但最终仍然要结合实际查询模式。

---

## 16. 过滤 + 范围 + 排序的联合索引

查询：

```sql
SELECT *
FROM orders
WHERE user_id = 1001
  AND status = 'PAID'
  AND created_at >= '2026-09-01'
ORDER BY created_at DESC;
```

候选索引：

```text
A. (user_id, status, created_at)
B. (created_at, user_id, status)
C. (status, created_at, user_id)
```

本轮选择：

```text
A
```

原因：

```text
user_id = 1001
→ 等值

status = 'PAID'
→ 等值

created_at >= ...
→ 范围
```

同时，当前两个字段固定后，当前索引范围内部已经按照：

```text
created_at
```

有序。

所以可以利用该顺序完成：

```sql
ORDER BY created_at DESC
```

本轮提到 MySQL 可以反向扫描索引来满足倒序需求，因此通常不需要额外：

```text
Using filesort
```

---

### 16.1 为什么 type 仍然可能是 range

虽然：

```text
user_id
status
```

都是等值条件，但最后：

```sql
created_at >= ...
```

是范围条件。

所以整体访问方式仍可能表现为：

```text
type = range
```

可以理解为：

```text
user_id = ?     等值
status = ?      等值
created_at >= ? 范围
                ↑
              到这里进入 range
```

---

### 16.2 SELECT * 仍可能回表

即使：

```sql
(user_id, status, created_at)
```

非常适合：

- 过滤
- 范围扫描
- 排序

但：

```sql
SELECT *
```

还需要：

```text
amount
```

等联合索引里没有的字段。

因此仍然可能：

```text
联合索引负责定位和排序
↓
拿主键
↓
回表取完整订单
```

索引设计好并不等于一定不回表。

---

## 17. ORDER BY + LIMIT 为什么特别适合配合索引

查询：

```sql
SELECT *
FROM orders
WHERE user_id = 1001
  AND status = 'PAID'
  AND created_at >= '2026-09-01'
ORDER BY created_at DESC
LIMIT 20;
```

如果有：

```sql
INDEX idx_user_status_created(user_id, status, created_at)
```

数据库可以近似：

```text
定位符合条件的索引范围
↓
从 created_at 较大的一侧开始扫描
↓
找到一条，处理一条
↓
累计 20 条
↓
停止
```

因此：

> 索引顺序与 `ORDER BY + LIMIT` 配合时，可以让查询更早停止。

反过来，如果只有：

```sql
INDEX idx_user_status(user_id, status)
```

虽然可以很快找到：

```text
user_id = 1001
status = PAID
```

但这些记录没有按 `created_at` 排序。

如果命中 10 万条，可能需要：

```text
处理大量候选记录
↓
按 created_at 额外排序
↓
最后只取 20 条
```

所以：

> `LIMIT 20` 不代表数据库只处理 20 条记录。

关键要看能不能直接按所需顺序拿到这 20 条。

---

## 18. 深分页

例如：

```sql
SELECT *
FROM orders
WHERE user_id = 1001
ORDER BY created_at DESC
LIMIT 20 OFFSET 100000;
```

即使有：

```sql
(user_id, created_at)
```

仍可能越来越慢。

因为 `OFFSET 100000` 可以粗略理解为：

```text
按照索引顺序找到数据
↓
前 100000 条跳过
↓
再取 20 条
```

所以：

```text
返回 20 条
≠
只处理 20 条
```

数据库可能需要先走过：

```text
100020 条索引记录
```

---

### 18.1 Keyset / Seek Pagination

本轮给出的思路是：

> 记录上一页最后一条记录的位置，然后下一页直接从这个位置继续查。

例如上一页最后一条：

```text
created_at = '2026-09-01 12:30:00'
id = 98765
```

下一页不再：

```sql
LIMIT 20 OFFSET 100000
```

而是类似：

```sql
WHERE user_id = 1001
  AND created_at < '2026-09-01 12:30:00'
ORDER BY created_at DESC
LIMIT 20;
```

思路变成：

```text
直接从上一页之后的位置继续找
↓
取 20 条
↓
停止
```

本轮将这种方式称为：

```text
Keyset Pagination
Seek Pagination
游标式分页
```

---

### 18.2 created_at 相同的边界问题

如果不同订单的：

```text
created_at
```

可能相同，只靠：

```sql
created_at < ?
```

可能漏数据。

因此本轮提到更稳的思路是设计：

```sql
INDEX (user_id, created_at, id)
```

并结合：

```text
(created_at, id)
```

作为稳定分页位置。

本轮没有继续展开具体 SQL。

---

## 19. 两个单列索引不等于一个联合索引

假设：

```sql
INDEX idx_user(user_id)
INDEX idx_status(status)
```

查询：

```sql
WHERE user_id = 1001
  AND status = 'PAID'
```

这两个索引是两棵独立的 B+Tree。

而：

```sql
INDEX idx_user_status(user_id, status)
```

是在一棵树中建立：

```text
先 user_id
再 status
```

的有序关系。

所以：

> 两个单列索引不能简单等价于一个联合索引。

---

## 20. Index Merge

MySQL 有时可以同时利用多个单列索引。

例如：

```text
idx_user
→ 得到一组主键 id

idx_status
→ 得到另一组主键 id

两边求交集
→ 得到同时满足条件的 id
→ 再回表
```

`EXPLAIN` 可能出现：

```text
type = index_merge
key = idx_user,idx_status
```

所以：

> MySQL 确实有能力同时利用多个单列索引。

但是不能因此得出：

> 以后全部建立单列索引，交给 Index Merge 即可。

本轮认为对于稳定、高频的组合查询：

> 联合索引通常优于依赖 Index Merge。

因为联合索引可以在一棵树中直接定位目标范围，而 Index Merge 要分别查索引、收集主键、合并或求交集，再访问数据。

---

### 20.1 两个单列索引无法替代联合索引的排序能力

查询：

```sql
SELECT *
FROM orders
WHERE user_id = 1001
ORDER BY created_at DESC
LIMIT 20;
```

如果只有：

```sql
INDEX(user_id)
INDEX(created_at)
```

这两个索引并不能自动组合成：

```sql
INDEX(user_id, created_at)
```

因为：

```text
(user_id, created_at)
```

表达的是：

> 在同一个 `user_id` 内部，`created_at` 继续有序。

而两个单列索引只能分别表达：

```text
哪些记录属于 user_id=1001
```

和：

```text
整张表的 created_at 顺序
```

它们没有建立：

```text
user_id=1001 这一组内部的 created_at 顺序
```

---

## 21. 联合索引真正重要的是“层级有序”

例如：

```sql
INDEX (user_id, created_at)
```

可以理解成：

```text
先按 user_id 分组排序
每个 user_id 内部
再按 created_at 排序
```

所以：

```sql
WHERE user_id = ?
ORDER BY created_at
```

特别适合这个联合索引。

这也解释了为什么联合索引不仅仅是：

> “一次可以查多个字段”。

更重要的是：

> 后面的列是在前面的列已经确定的前提下继续有序。

---

## 22. 为什么联合索引不是越宽越好

假设建立：

```sql
INDEX (
    user_id,
    status,
    created_at,
    amount,
    ...
)
```

希望尽量覆盖更多查询。

本轮讨论了几个成本。

---

### 22.1 索引本身会变大

例如：

```text
(user_id, status, created_at)
```

显然比：

```text
(user_id)
```

占用更多空间。

索引越大：

- 磁盘空间占用更高
- Buffer Pool 能缓存的索引页更少
- 一次读入的索引页中能容纳的索引记录也可能更少

因此宽索引可能间接增加 I/O。

---

### 22.2 写操作维护成本增加

每次：

```sql
INSERT
UPDATE
DELETE
```

相关索引也要维护。

例如：

```sql
UPDATE orders
SET status = 'PAID'
WHERE id = 100;
```

如果 `status` 在联合索引中，索引结构也要随之更新。

所以：

> 索引越多、越宽，写操作通常成本越高。

本轮形成的直觉是：

```text
读多写少
→ 可以更积极建索引

写入频繁
→ 更需要谨慎
```

---

### 22.3 不要为了 Using index 机械扩宽索引

例如：

```sql
SELECT amount
FROM orders
WHERE user_id = ?
ORDER BY created_at DESC
LIMIT 20;
```

为了完全不回表，可以考虑：

```sql
(user_id, created_at, amount)
```

但必须问：

> 为了省很少量回表，是否值得让整个索引都额外保存 `amount`？

如果只取 20 行，本轮认为：

```sql
(user_id, created_at)
```

可能已经足够。

所以：

> 不要为了追求 `Using index`，机械地把所有 `SELECT` 字段都塞进联合索引。

---

### 22.4 “索引里有字段”不等于“这个字段能用于定位”

例如：

```sql
INDEX(user_id, status, created_at, amount)
```

查询：

```sql
WHERE user_id = ?
  AND created_at > ?
```

虽然：

```text
created_at
```

确实存在于索引中，但中间跳过了：

```text
status
```

所以它未必能像：

```sql
(user_id, created_at)
```

那样直接参与范围定位。

因此必须区分：

```text
字段存在于索引中
```

和：

```text
字段能参与缩小 B+Tree 搜索范围
```

这两个概念不同。

---

## 23. 索引设计不是追求“索引利用率最高”

本轮形成的一个重要观念是：

> 索引设计的目标不是让所有 SQL 都显示“用了索引”或者都出现 `Using index`，而是让整体查询成本更合理。

例如：

```text
扫描 20 条索引
+
回表 20 次
```

完全可能比：

```text
为了避免这 20 次回表
维护一个很大的联合索引
```

更划算。

所以：

> 偶尔回表不一定是坏事。

索引设计应该综合考虑：

- 查询模式
- 扫描范围
- 排序需求
- 回表成本
- 索引大小
- 写入维护成本

---

## 24. rows 很小不代表 SQL 一定快

`rows` 主要说明：

> 优化器预计需要检查多少行。

它不能完整表达所有实际耗时来源。

---

### 24.1 回表仍然有成本

例如：

```sql
SELECT *
FROM orders
WHERE user_id = 1001
LIMIT 20;
```

即使：

```text
rows = 20
```

仍然可能：

```text
二级索引
↓
得到 20 个主键
↓
回表读取完整记录
```

如果对应数据页已经在内存中，通常很快；如果涉及额外 I/O，则成本更高。

本轮同时指出：

> 20 条这种量通常不值得过度担心，真正需要警惕的是大量候选行配合大量回表。

---

### 24.2 排序和临时处理

例如：

```sql
SELECT *
FROM orders
WHERE user_id = 1001
ORDER BY amount DESC;
```

即使：

```text
rows = 500
```

仍然需要处理排序。

所以：

```text
rows
```

并不能单独反映：

```text
Using filesort
```

等额外成本。

---

### 24.3 单行本身可能很重

例如：

```sql
SELECT *
FROM article
WHERE id = 100;
```

即使：

```text
type = const
rows = 1
```

如果这一行里包含很大的：

```text
LONGTEXT
BLOB
JSON
```

读取、传输等仍然可能有成本。

因此：

```text
rows = 1
```

只说明定位的候选行少，不代表所有后续成本为零。

---

### 24.4 锁等待

假设事务 A：

```sql
UPDATE account
SET balance = balance - 100
WHERE id = 1;
```

锁住了目标记录。

事务 B：

```sql
UPDATE account
SET balance = balance + 100
WHERE id = 1;
```

即使执行计划非常漂亮：

```text
key = PRIMARY
rows = 1
```

仍可能因为锁等待而变慢。

所以：

> `EXPLAIN` 主要描述数据库准备如何访问数据，并不能解释所有运行时等待。

---

### 24.5 rows 是估算

普通：

```sql
EXPLAIN SELECT ...
```

中的 `rows` 是优化器估算值。

例如：

```text
rows = 100
```

实际执行时不一定就是 100。

本轮提到，如果数据分布非常不均匀，例如：

```text
status:
PAID      99%
CANCELLED 0.5%
PENDING   0.5%
```

仅知道字段有几种取值，并不能完整反映真实分布，因此优化器估计可能存在偏差。

---

## 25. EXPLAIN ANALYZE：本轮只到概念层

本轮最后只简单区分了：

```text
EXPLAIN
→ 优化器准备怎么执行
→ 主要是执行计划与估算

EXPLAIN ANALYZE
→ 实际执行 SQL
→ 能看到更多实际执行情况
```

可以用一个直观比喻：

```text
EXPLAIN
→ “我计划走这条路线，预计走 100 米”

EXPLAIN ANALYZE
→ “我真的走完了，实际走了多少、花了多少”
```

本轮认为：

> `EXPLAIN ANALYZE` 属于后续进阶内容，本轮先停在普通 `EXPLAIN`。

---

## 26. 本轮高频易错点汇总

### 26.1 `const` 和 `ref`

错误倾向：

```text
普通索引等值查询 → const
```

正确：

```text
唯一索引 / 主键等值 → const
普通索引等值       → ref
```

---

### 26.2 `ref` 不代表只返回一行

```sql
WHERE age = 20
```

如果 `age` 是普通索引：

```text
type = ref
```

即使有几千行 `age=20`。

---

### 26.3 `range` 不等于“返回很多行”

`range` 表示：

> 索引范围扫描。

而不是结果数量。

---

### 26.4 无索引条件不是 range

```sql
WHERE nickname = 'Tom'
```

如果 `nickname` 无索引：

```text
type = ALL
key = NULL
```

而不是 `range`。

---

### 26.5 `type=index`、`key=idx_xxx`、`Using index` 是三个概念

```text
type = index
→ 扫整个索引

key = idx_age
→ 实际使用 idx_age

Extra = Using index
→ 覆盖索引，不回表
```

---

### 26.6 `SELECT id` 不意味着改用主键索引

二级索引中本身带主键：

```text
(age, id)
```

所以：

```sql
SELECT id
FROM user
WHERE age = 20;
```

可以继续使用：

```text
idx_age
```

而不需要访问主键索引。

---

### 26.7 `Using where` 不等于回表

`Using where` 表示：

> 还需要应用 WHERE 条件过滤。

是否回表由：

> 当前索引是否覆盖查询需要的字段

决定。

---

### 26.8 范围条件后面的联合索引列不是“完全无效”

例如：

```sql
INDEX(age, username)
```

```sql
WHERE age > 20
  AND username = 'alice'
```

`username` 通常不能继续缩小整个 B+Tree 搜索范围，但仍可能通过：

```text
Using index condition
```

在索引层参与过滤。

---

### 26.9 对索引列做计算不能指望优化器自动化简

```sql
WHERE age + 1 = 21
```

不能简单认为数据库一定会自动变成：

```sql
WHERE age = 20
```

再使用 `idx_age`。

---

### 26.10 隐式类型转换不是“必然索引失效”

```sql
age INT
WHERE age = '20'
```

本轮认为索引很可能仍能使用。

但：

```sql
phone VARCHAR
WHERE phone = 13800138000
```

属于更危险的情况。

所以应尽量让 SQL 参数类型与列类型一致。

---

### 26.11 LIKE 不是“一律不能走索引”

```text
'abc%'  → 通常可以
'%abc'  → 通常不行
'%abc%' → 通常不行
```

关键是前导通配符。

---

### 26.12 `(a,b,c)` 中 c 存在，不代表跳过 b 后还能正常定位 c

必须区分：

```text
索引中保存了这个字段
```

和：

```text
这个字段能用于缩小索引搜索范围
```

---

### 26.13 联合索引不是越长越好

更宽的索引意味着：

- 更大的索引空间
- 更高的写入维护成本
- 更高的缓存压力

不应该单纯为了覆盖索引而机械增加列。

---

### 26.14 LIMIT 很小不代表查询处理的数据很少

例如：

```sql
LIMIT 20 OFFSET 100000
```

虽然最终只返回 20 条，但数据库可能需要先走过大量前置记录。

---

## 27. 本轮练习中形成的分析套路

以后看到一条 SQL，可以先按下面的顺序判断：

```text
1. WHERE 中哪些字段有索引？
2. 实际可能使用哪个 key？
3. 等值查询还是范围查询？
   =           → 常见 ref
   > < BETWEEN → 常见 range
4. 是否跳过了联合索引左侧字段？
5. 是否遇到范围条件后还试图继续利用后续字段？
6. SELECT 字段是否被当前索引覆盖？
   → 是否需要回表？
7. WHERE 中是否还有可以在索引层过滤的条件？
   → 是否可能出现 ICP？
8. ORDER BY 是否符合联合索引现有排序？
   → 是否可能 Using filesort？
9. rows 是多少？
   → 扫描范围是否过大？
10. 是否为了避免少量回表而设计了过宽索引？
```

---

## 28. 本轮综合示例

假设：

```sql
CREATE TABLE user (
    id BIGINT PRIMARY KEY,
    username VARCHAR(50),
    age INT,
    city VARCHAR(50),

    INDEX idx_age_username(age, username),
    INDEX idx_city(city)
);
```

### 示例 1

```sql
SELECT username
FROM user
WHERE age = 20;
```

分析：

```text
type = ref
key = idx_age_username
```

联合二级索引可粗略理解为：

```text
(age, username, id)
```

因此：

- `age` 用于等值定位
- `username` 直接从索引取得
- 不需要回表
- 可能出现 `Using index`

---

### 示例 2

```sql
SELECT *
FROM user
WHERE age > 20
  AND username = 'alice';
```

分析：

```text
type = range
key = idx_age_username
```

- `age > 20` 确定索引范围
- `username` 不能继续缩小为全局连续范围
- 但可能通过 ICP 在索引层过滤
- `SELECT *` 需要 `city` 等完整字段
- 因此需要回表
- 没有 `ORDER BY`，不涉及 filesort

---

### 示例 3

```sql
SELECT id, username
FROM user
WHERE age = 20
ORDER BY username;
```

分析：

```text
type = ref
key = idx_age_username
```

- `age = 20` 等值定位
- `(age, username, id)` 覆盖查询字段
- 不回表
- `age=20` 固定后，`username` 天然有序
- 不需要额外 filesort

---

### 示例 4

```sql
SELECT *
FROM user
WHERE city = 'Shenzhen'
ORDER BY age;
```

有：

```sql
INDEX idx_city(city)
```

分析：

```text
type = ref
key = idx_city
```

但：

```text
idx_city
```

只能粗略看作：

```text
(city, id)
```

没有提供：

```text
city 内部按 age 排序
```

所以：

- `city='Shenzhen'` 可以用 `idx_city`
- `SELECT *` 需要回表
- `ORDER BY age` 通常需要额外排序
- 可能出现 `Using filesort`

---

## 29. 本轮学习边界

本轮已经覆盖：

- `possible_keys`
- `key`
- `rows`
- `Extra`
- `const`
- `ref`
- `range`
- `index`
- `ALL`
- 二级索引包含主键的理解模型
- 回表
- 覆盖索引
- `Using index`
- `Using where`
- `Using index condition`
- ICP
- 索引列上的计算
- 隐式类型转换
- `LIKE`
- 联合索引最左前缀
- 范围条件对后续索引列的影响
- `key_len` 的基础含义
- `Using filesort`
- `Using temporary`
- 联合索引字段顺序
- 索引冗余
- `ORDER BY + LIMIT`
- 深分页
- Keyset / Seek Pagination
- Index Merge
- 两个单列索引与联合索引的差异
- 宽索引的成本
- `rows` 很小但 SQL 仍可能慢的原因

本轮没有继续深入：

```text
EXPLAIN ANALYZE
```

只保留了它和普通 `EXPLAIN` 的基础区别，后续再作为进阶内容学习。
