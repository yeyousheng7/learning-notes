# MySQL EXPLAIN 实操复盘笔记

## 1. 在线实验环境与实验方式

本次学习使用在线 MySQL 环境直接执行 `EXPLAIN`，重点不是背字段，而是通过“修改索引 / 修改 SQL / 对比执行计划”建立直觉。

一开始在线环境曾出现：

```text
E001: operation timed out
```

结合后续同一环境能够正常运行，以及当时 SQL 只有几行数据，可以判断这次超时更像是在线环境本身启动、连接或后端实例超时，而不是 SQL 本身执行超时。

本次实验主要围绕下面这张表展开：

```sql
CREATE TABLE employee (
    emp_id INT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    dept VARCHAR(30) NOT NULL,
    age INT NOT NULL,
    salary INT NOT NULL
);
```

示例数据：

```sql
INSERT INTO employee VALUES
(1, 'Clark', 'Sales',       25,  6000),
(2, 'Dave',  'Accounting',  30,  8000),
(3, 'Ava',   'Sales',       28,  7000),
(4, 'Bob',   'Tech',        24,  9000),
(5, 'Alice', 'Tech',        32, 10000);
```

后续逐步建立过这些索引：

```sql
CREATE INDEX idx_dept ON employee(dept);
CREATE INDEX idx_dept_age ON employee(dept, age);
CREATE INDEX idx_age ON employee(age);
CREATE INDEX idx_salary ON employee(salary);
CREATE INDEX idx_dept_salary ON employee(dept, salary);
```

还建立了部门表用于 JOIN 实验：

```sql
CREATE TABLE department (
    dept_id INT PRIMARY KEY,
    dept_name VARCHAR(30) NOT NULL UNIQUE
);
```

```sql
INSERT INTO department VALUES
(1, 'Sales'),
(2, 'Accounting'),
(3, 'Tech');
```

---

## 2. 阅读 EXPLAIN 的基本顺序

本次学习中形成的阅读顺序是：

```text
这条 SQL 怎么找数据？
        ↓
type：访问方式是什么？
        ↓
possible_keys：哪些索引可能有价值？
        ↓
key：最终实际用了哪个索引？
        ↓
rows：预计需要检查多少行？
        ↓
filtered：预计有多少比例的候选行能继续保留？
        ↓
Extra：是否存在额外执行信息？
```

当前阶段重点关注：

```text
type
possible_keys
key
key_len
ref
rows
filtered
Extra
```

其中 `select_type` 也做了基础理解，但不是当前最核心字段。

---

## 3. `type`：表 / 索引访问方式

本次实际跑到的主要类型：

```text
ALL
index
range
ref
eq_ref
const
```

这些类型不是简单地表示“有没有索引”，而是在描述 MySQL 如何访问当前表或索引。

---

### 3.1 `ALL`：全表扫描

实验：

```sql
EXPLAIN
SELECT *
FROM employee
WHERE dept = 'Sales';
```

在没有 `dept` 索引时得到：

```text
type          = ALL
possible_keys = NULL
key           = NULL
```

可以理解为：

```text
没有可用于 dept='Sales' 的索引
        ↓
扫描 employee 全表
        ↓
逐行判断 dept = 'Sales'
```

所以：

```text
type = ALL
```

表示全表扫描。

另一个实验：

```sql
EXPLAIN
SELECT *
FROM employee
WHERE age > 26;
```

当只有联合索引：

```text
idx_dept_age(dept, age)
```

而查询只使用第二列 `age` 时，结果也是：

```text
type          = ALL
possible_keys = NULL
key           = NULL
rows          = 5
filtered      = 33.33
Extra         = Using where
```

这验证了联合索引最左列的重要性：仅使用第二列 `age` 时，现有 `(dept, age)` 不能直接提供一个合适的连续扫描范围。

---

### 3.2 `index`：全索引扫描

这是本次非常容易和 `Using index` 混淆的地方。

```text
type = index
```

表示：

> 扫描整个索引。

它和 `ALL` 的共同点是都可能“全部扫描”，区别是扫描对象不同：

```text
ALL   → 全表扫描
index → 全索引扫描
```

例如：

```sql
EXPLAIN
SELECT salary
FROM employee
ORDER BY salary;
```

有索引：

```text
idx_salary(salary)
```

实际得到：

```text
type          = index
possible_keys = NULL
key           = idx_salary
rows          = 6
filtered      = 100.00
Extra         = Using index
```

这里：

```text
type = index
```

表示整个 `idx_salary` 都要扫。

另外，在：

```sql
SELECT dept, COUNT(*)
FROM employee
GROUP BY dept;
```

有：

```text
idx_dept(dept)
```

时也得到：

```text
type = index
key  = idx_dept
Extra = Using index
```

说明 MySQL 顺序扫描整个 `dept` 索引，并利用索引顺序完成分组。

#### 易错点

```text
type = index
```

和：

```text
Extra = Using index
```

完全不是一回事。

- `type = index`：全索引扫描。
- `Using index`：覆盖索引，不需要回表。

两者可以同时出现，也可以只出现其中一个。

---

### 3.3 `range`：索引范围扫描

实验：

```sql
CREATE INDEX idx_age ON employee(age);

EXPLAIN
SELECT *
FROM employee
WHERE age > 26;
```

结果：

```text
type          = range
possible_keys = idx_age
key           = idx_age
rows          = 3
filtered      = 100.00
Extra         = Using index condition
```

因为：

```sql
age > 26
```

是范围条件，可以在 `idx_age` 中定位一个连续范围，而不是扫描整个索引。

另一个实验：

```sql
EXPLAIN
SELECT *
FROM employee FORCE INDEX (idx_dept_age)
WHERE dept = 'Sales'
  AND age > 26;
```

结果：

```text
type     = range
key      = idx_dept_age
rows     = 1
filtered = 100
Extra    = Using index condition
```

联合索引：

```text
(dept, age)
```

面对：

```text
dept = 'Sales'
AND age > 26
```

可以先固定 `dept = Sales`，再在该范围内处理 `age > 26`，因此出现 `range`。

---

### 3.4 `ref`：普通索引等值查询

实验：

```sql
CREATE INDEX idx_dept ON employee(dept);

EXPLAIN
SELECT *
FROM employee
WHERE dept = 'Sales';
```

得到：

```text
type          = ref
possible_keys = idx_dept
key           = idx_dept
rows          = 2
filtered      = 100.00
```

这里的核心是：

> 拿一个值通过普通索引做等值查询，而一个值可能对应多行。

例如：

```text
dept = 'Sales'
```

可能对应：

```text
Clark
Ava
```

所以属于 `ref`。

在 JOIN 中也出现了 `ref`：

```sql
EXPLAIN
SELECT e.name, d.dept_id
FROM employee e
JOIN department d
    ON e.dept = d.dept_name;
```

优化器实际先访问 `department d`，再访问 `employee e`：

```text
d:
type = index
key  = dept_name

e:
type = ref
key  = idx_dept_age
ref  = d.dept_name
```

这里第二行相当于：

```text
拿当前 d.dept_name
        ↓
去 employee 的 dept 索引中做等值查询
```

它本质上和：

```sql
WHERE dept = 'Sales'
```

一样，只是右边的值不再是固定常量，而是来自前一张表。

---

### 3.5 `eq_ref`：JOIN 中的唯一等值查询

为了固定 JOIN 顺序，本次实验使用：

```sql
EXPLAIN
SELECT e.name, d.dept_id
FROM employee e
STRAIGHT_JOIN department d
    ON e.dept = d.dept_name;
```

结果：

```text
e:
type = ALL

d:
type = eq_ref
key  = dept_name
ref  = e.dept
rows = 1
Extra = Using index
```

`department.dept_name` 是：

```sql
UNIQUE
```

所以对 `employee` 中每一行：

```text
拿 e.dept
    ↓
查询 d.dept_name = e.dept
    ↓
最多只能匹配一行
```

因此：

```text
type = eq_ref
```

#### `ref` 与 `eq_ref`

```text
ref
→ 等值索引查询
→ 可能返回多行

eq_ref
→ JOIN 中用唯一索引做等值查询
→ 对前表的每一行，最多匹配一行
```

---

### 3.6 `const`：固定常量唯一定位

实验：

```sql
EXPLAIN
SELECT *
FROM employee
WHERE emp_id = 3;
```

`emp_id` 是主键，结果：

```text
type          = const
possible_keys = PRIMARY
key           = PRIMARY
rows          = 1
filtered      = 100
Extra         = NULL
```

这里：

```text
emp_id = 3
```

是一个固定常量，MySQL 可以直接唯一定位这一行。

#### `const`、`eq_ref`、`ref` 的区别

```text
const
→ 用固定常量唯一定位

eq_ref
→ JOIN 中，用前一张表当前行提供的值唯一定位

ref
→ 用某个值做普通索引等值查询，可能匹配多行
```

---

## 4. `possible_keys` 与 `key`

最初容易产生的理解是：

> `possible_keys` 和 `key` 都主要描述 WHERE。

这个理解后来被实验修正。

更稳妥的理解是：

```text
possible_keys
→ 优化器认为当前查询中可能有价值的候选索引

key
→ 最终执行计划实际选择的索引
```

例如：

```sql
SELECT salary
FROM employee
ORDER BY salary;
```

得到：

```text
possible_keys = NULL
key           = idx_salary
```

这说明：

> `possible_keys = NULL` 并不意味着最终一定不会使用索引。

这里没有 `WHERE`，但优化器仍然可以实际选择 `idx_salary`，因为索引顺序能帮助 `ORDER BY`，同时又能覆盖查询。

另一个实验：

```sql
SELECT dept, COUNT(*)
FROM employee
GROUP BY dept;
```

没有 `WHERE`，仍然得到：

```text
possible_keys = idx_dept_age, idx_dept
key           = idx_dept
```

因此不能把 `possible_keys` 简单记成“WHERE 专属字段”。

---

## 5. `rows` 与 `filtered`

### 5.1 `rows`

`rows` 表示优化器预计当前访问方式需要检查的行数。

例如：

```sql
SELECT *
FROM employee
WHERE dept = 'Sales';
```

使用 `idx_dept`：

```text
rows = 2
```

因为预计找到两个 `Sales`。

建立联合索引后：

```sql
SELECT *
FROM employee FORCE INDEX(idx_dept_age)
WHERE dept = 'Sales'
  AND age > 26;
```

得到：

```text
rows = 1
```

因为联合索引能进一步缩小范围。

#### 易错点

`range` 不意味着 `rows` 一定很多。

`rows` 取决于优化器估计的扫描范围大小，而不是单纯由 `type` 名字决定。

---

### 5.2 `filtered`

最初通过实验形成的理解：

> `filtered` 可以理解为经过当前访问方式得到的候选记录中，预计有多少比例能继续通过过滤。

例如：

```sql
SELECT *
FROM employee
WHERE dept = 'Sales'
  AND age > 26;
```

只有 `idx_dept(dept)` 时：

```text
type     = ref
rows     = 2
filtered = 33.33
Extra    = Using where
```

大致可以理解为：

```text
先通过 dept 索引找到候选行
        ↓
rows ≈ 2
        ↓
再判断 age > 26
        ↓
预计约 33.33% 保留
```

可以粗略理解：

```text
最终预计结果行数
≈ rows × filtered / 100
```

例如：

```text
2 × 33.33% ≈ 0.67
```

这里不是实际结果统计，而是优化器估计。

实际数据中 `Sales` 有两行：

```text
Clark age=25
Ava   age=28
```

真正满足 `age > 26` 的是 1 / 2，即 50%，但 `filtered` 显示 33.33%。

因此：

> `rows` 和 `filtered` 都应主要理解为优化器估计，而不是实际运行后的精确统计。

小数据下估计和真实比例不一致是本次实验中实际出现过的情况。

---

## 6. `Extra`：常见信息与易混淆点

本次重点遇到：

```text
Using where
Using index
Using index condition
Using filesort
Using temporary
Backward index scan
NULL
```

---

### 6.1 `Using where`

最初容易产生的误解：

> `Using where` = WHERE 条件没有利用索引，只能在拿到数据行后额外过滤。

这个理解后来通过实验修正。

例如：

```sql
SELECT age
FROM employee
WHERE age > 26;
```

执行计划：

```text
type  = range
key   = idx_age
Extra = Using where; Using index
```

这里明明已经通过：

```text
type = range
key  = idx_age
```

利用 `age > 26` 做索引范围访问，但仍然出现 `Using where`。

因此更稳妥的理解是：

> `Using where` 表示 MySQL 仍然需要应用 `WHERE` 条件进行判断。

不能仅凭 `Using where` 推断：

```text
没有走索引
一定先回表再过滤
发生了全表扫描
```

判断索引是否参与定位，应结合：

```text
type
key
key_len
rows
```

来看。

#### 一个没有 `Using where` 的例子

```sql
SELECT dept, age
FROM employee
WHERE dept = 'Sales'
ORDER BY salary;
```

使用：

```text
idx_dept_salary(dept, salary)
```

得到：

```text
type = ref
key  = idx_dept_salary
Extra = NULL
```

这里唯一的 WHERE 条件：

```text
dept = 'Sales'
```

已经直接用于索引访问，没有额外残余条件需要特别标注。

---

### 6.2 `Using index`：覆盖索引

这是本次反复追问、最容易混淆的概念之一。

```text
Using index
```

不是：

```text
“用了索引”
```

也不是：

```text
“索引用得很充分”
```

它表示：

> 查询需要的数据可以直接由索引提供，不需要回表。

例如：

```sql
SELECT age
FROM employee
WHERE age > 26;
```

索引：

```text
idx_age(age)
```

查询条件和返回字段都只需要 `age`，因此索引本身已经够用。

又例如：

```sql
SELECT dept, COUNT(*)
FROM employee
GROUP BY dept;
```

使用 `idx_dept(dept)` 时：

```text
Extra = Using index
```

因为整个查询可以只依靠该索引完成。

#### 重要区分

```text
type = index
→ 全索引扫描

Using index
→ 覆盖索引，不回表
```

两者名字很像，但含义完全不同。

---

### 6.3 回表与主键聚簇索引

实验：

```sql
SELECT *
FROM employee
WHERE emp_id = 3;
```

得到：

```text
type  = const
key   = PRIMARY
Extra = NULL
```

用户曾疑问：

> `SELECT *` 应该需要回表，为什么 `Extra` 是 `NULL`？

本次讨论中的理解是：

InnoDB 的主键索引是聚簇索引，叶子节点本身保存完整数据行。

所以主键查询可以理解为：

```text
PRIMARY B+Tree
    ↓
定位 emp_id = 3
    ↓
叶子节点就是完整记录
    ↓
直接返回
```

不需要经历：

```text
二级索引
    ↓
得到主键
    ↓
再去 PRIMARY 找完整数据行
```

后者才是本次讨论中所说的“回表”。

例如：

```sql
SELECT *
FROM employee
WHERE age > 26;
```

走二级索引 `idx_age(age)` 时，因为查询还需要 `name/dept/salary` 等字段，所以需要根据二级索引中的主键信息再找到完整记录。

#### `Extra = NULL`

`Extra = NULL` 不表示：

```text
什么都没做
```

也不表示：

```text
没有读取数据行
```

它只是表示没有额外值得写入 `Extra` 的执行信息。

因此：

```text
Extra = NULL
```

完全可能出现在非常高效的主键 `const` 查询里。

---

### 6.4 `Using index condition`：ICP

`Using index condition` 对应本次讨论中的 ICP（Index Condition Pushdown，索引条件下推）。

本次建立的理解：

> 使用索引以后，把能够利用索引中已有字段判断的条件尽量提前到索引层处理，从而减少不必要的回表。

例如：

```sql
SELECT *
FROM employee
WHERE age > 26;
```

有：

```text
idx_age(age)
```

得到：

```text
type  = range
key   = idx_age
Extra = Using index condition
```

因为 `SELECT *` 不能被 `idx_age` 覆盖，最终仍需要完整数据行，但索引中的 `age` 可以参与提前判断。

#### `Using index condition` ≠ 使用了索引

索引是否被使用主要看：

```text
key
type
```

ICP 是“已经在使用索引之后”的进一步优化行为。

#### `Using index condition` 与 `Using index`

```text
Using index condition
→ ICP
→ 重点是利用索引提前过滤，减少回表

Using index
→ 覆盖索引
→ 重点是不需要回表
```

#### 为什么有时条件在索引里，却没有 ICP？

综合题：

```sql
SELECT dept, COUNT(*) AS cnt
FROM employee
WHERE age > 26
GROUP BY dept
ORDER BY dept DESC;
```

执行计划：

```text
type     = index
key      = idx_dept_age
filtered = 50.00
Extra    = Using where; Backward index scan; Using index
```

这里 `age` 明明在 `(dept, age)` 索引中，却没有出现 `Using index condition`。

本次讨论中得到的解释是：

```text
Using index
```

已经说明查询被索引覆盖，本来就不需要回表。

而 ICP 的主要价值是：

```text
在回表之前利用索引过滤
→ 减少回表次数
```

如果根本不回表，这一价值就没有意义。

因此：

> “条件字段在索引里”不意味着一定会出现 ICP。

---

### 6.5 `Using filesort`

实验：

```sql
EXPLAIN
SELECT *
FROM employee
ORDER BY salary;
```

没有 `salary` 索引时：

```text
type  = ALL
key   = NULL
Extra = Using filesort
```

表示：

> 不能直接利用索引顺序满足 `ORDER BY`，需要额外排序。

#### 易错点

```text
Using filesort
```

不等于：

```text
一定写磁盘文件排序
```

本次学习中将它理解为：

> 需要额外排序，而不是直接顺着现有索引顺序输出。

它也不等于“一定很慢”。

---

### 6.6 `Using temporary`

实验：

```sql
SELECT dept, salary, COUNT(*)
FROM employee
GROUP BY dept, salary;
```

在只有：

```text
idx_dept(dept)
idx_salary(salary)
idx_dept_age(dept, age)
```

而没有：

```text
(dept, salary)
```

时，结果：

```text
type  = ALL
key   = NULL
Extra = Using temporary
```

本次学习中对它的理解是：

> MySQL 需要额外的临时中间结构来组织分组结果。

另一个更典型实验：

```sql
SELECT dept, COUNT(*) AS cnt
FROM employee
GROUP BY dept
ORDER BY cnt DESC;
```

得到：

```text
type  = index
key   = idx_dept
Extra = Using index; Using temporary; Using filesort
```

逻辑可以理解为：

```text
扫描 idx_dept
        ↓
完成 dept 分组并计算 COUNT(*)
        ↓
形成类似：
dept | cnt
        ↓
临时结构保存中间聚合结果
        ↑
Using temporary
        ↓
再按 cnt DESC 排序
        ↑
Using filesort
```

这里 `cnt` 是聚合以后才产生的值，原索引中不存在“按 cnt 排好”的顺序，所以需要先聚合，再保存中间结果，再排序。

#### 易错点

`Using temporary` 不等于一定创建了磁盘临时表。

本次学习中只把它理解为：

> 需要额外中间结构。

---

### 6.7 `Backward index scan`

实验：

```sql
SELECT dept, COUNT(*)
FROM employee
GROUP BY dept
ORDER BY dept DESC;
```

得到：

```text
Extra = Backward index scan; Using index
```

含义：

> 为满足降序要求，MySQL 反向遍历索引。

例如索引正常顺序：

```text
Accounting
Sales
Tech
```

反向扫描：

```text
Tech
Sales
Accounting
```

因此：

```text
Backward index scan
```

表示反向索引扫描。

---

## 7. `select_type`

最初的疑问：

> `SIMPLE` 是不是代表普通查询，出现 `GROUP BY` 就不是 SIMPLE？

本次得到的结论：

```text
SIMPLE
```

并不是“没有 GROUP BY / ORDER BY”。

它更接近：

> 查询中没有 UNION，也没有需要单独执行的子查询。

因此下面这些即使有：

```text
GROUP BY
ORDER BY
HAVING
JOIN
```

只要查询结构仍然是单一查询块，也可能是：

```text
select_type = SIMPLE
```

本次还提到：

```text
PRIMARY
→ 复杂查询中的最外层 SELECT

SUBQUERY
→ 子查询

UNION
→ UNION 后面的 SELECT
```

当前阶段只需理解 `select_type` 描述的是当前这一行执行计划中的 `SELECT` 在整个 SQL 里的角色。

---

## 8. 联合索引与最左前缀

索引：

```text
idx_dept_age(dept, age)
```

可以理解成：

```text
先按 dept 排
dept 相同时，再按 age 排
```

例如：

```text
Accounting, 30
Sales,      25
Sales,      28
Tech,       24
Tech,       32
```

---

### 8.1 使用第一列

```sql
WHERE dept = 'Sales'
```

可以直接找到：

```text
Sales, 25
Sales, 28
```

所以联合索引第一列可以正常用于索引访问。

---

### 8.2 第一列等值 + 第二列范围

```sql
WHERE dept = 'Sales'
  AND age > 26
```

联合索引可以：

```text
先定位 Sales
    ↓
再在 Sales 段中处理 age > 26
```

使用 `FORCE INDEX(idx_dept_age)` 后实际看到：

```text
type     = range
key      = idx_dept_age
rows     = 1
filtered = 100
Extra    = Using index condition
```

---

### 8.3 只使用第二列

```sql
WHERE age > 26
```

如果只有：

```text
(dept, age)
```

而没有 `idx_age(age)`，实际得到：

```text
type          = ALL
possible_keys = NULL
key           = NULL
```

原因是联合索引整体先按 `dept` 排序，`age` 只在同一个 `dept` 范围内有序，并不是全局按 `age` 排序。

因此无法直接得到一个全局连续的：

```text
age > 26
```

扫描范围。

本次还提到 MySQL 8 在某些情况下存在 `Index Skip Scan` 这一边界，但当前实验没有继续展开，实际测试结果仍然是 `ALL`。

---

## 9. 多个单列索引 ≠ 一个联合索引

实验：

```sql
SELECT dept, salary, COUNT(*)
FROM employee
GROUP BY dept, salary;
```

只有：

```text
INDEX(dept)
INDEX(salary)
```

并不能得到：

```text
INDEX(dept, salary)
```

的联合顺序。

原因是：

```text
INDEX(dept)
```

只能保证 `dept` 有序，而同一个 `dept` 内的 `salary` 不一定按索引顺序排列。

同理：

```text
INDEX(salary)
```

只保证 `salary` 有序，不能保证 `(dept, salary)` 的联合顺序。

因此当时执行计划：

```text
type  = ALL
key   = NULL
Extra = Using temporary
```

建立：

```sql
CREATE INDEX idx_dept_salary
ON employee(dept, salary);
```

以后重新执行：

```sql
SELECT dept, salary, COUNT(*)
FROM employee
GROUP BY dept, salary;
```

变成：

```text
type          = index
possible_keys = idx_dept_salary
key           = idx_dept_salary
rows          = 5
filtered      = 100
Extra         = Using index
```

联合索引天然按：

```text
dept → salary
```

组织，因此相同 `(dept, salary)` 组合连续，可以直接顺序扫描完成分组。

---

## 10. 索引为什么能帮助 GROUP BY

### 10.1 `GROUP BY dept`

查询：

```sql
SELECT dept, COUNT(*)
FROM employee
GROUP BY dept;
```

有：

```text
idx_dept(dept)
```

实际得到：

```text
type  = index
key   = idx_dept
Extra = Using index
```

索引中同一个 `dept` 的记录天然连续：

```text
Accounting
Sales
Sales
Tech
Tech
```

所以可以边扫描边统计：

```text
Accounting → 统计
Sales      → 开始统计
Sales      → 累加
Tech       → 开始下一组
```

不需要额外 `Using temporary`。

---

### 10.2 `GROUP BY dept, salary`

没有 `(dept, salary)` 联合索引时：

```text
Using temporary
```

建立：

```text
idx_dept_salary(dept, salary)
```

以后：

```text
Using temporary
```

消失，改为：

```text
Using index
```

这验证了：

> 索引顺序如果与分组组合一致，可以直接帮助 GROUP BY。

---

### 10.3 `GROUP BY dept ORDER BY cnt`

查询：

```sql
SELECT dept, COUNT(*) AS cnt
FROM employee
GROUP BY dept
ORDER BY cnt DESC;
```

结果：

```text
Using index; Using temporary; Using filesort
```

原因不是 `GROUP BY dept` 无法利用索引，而是：

```text
cnt
```

是聚合以后才产生的值。

必须先得到：

```text
dept | cnt
```

这样的中间结果，再按 `cnt` 排序。

---

### 10.4 `GROUP BY dept ORDER BY dept`

查询：

```sql
SELECT dept, COUNT(*) AS cnt
FROM employee
GROUP BY dept
ORDER BY dept;
```

由于 `GROUP BY` 与 `ORDER BY` 都对应 `dept`，可以利用 `idx_dept` 的顺序。

在降序情况下：

```sql
ORDER BY dept DESC
```

实际出现：

```text
Backward index scan; Using index
```

说明反向扫描同一个索引即可满足降序，不需要 `Using filesort`。

---

## 11. 索引为什么能帮助 ORDER BY

### 11.1 没有对应索引

```sql
SELECT *
FROM employee
ORDER BY salary;
```

最初：

```text
type  = ALL
key   = NULL
Extra = Using filesort
```

表示：

```text
读出数据
    ↓
额外按 salary 排序
```

---

### 11.2 建了索引，但优化器仍不使用

建立：

```sql
CREATE INDEX idx_salary ON employee(salary);
```

重新执行：

```sql
SELECT *
FROM employee
ORDER BY salary;
```

小数据情况下仍然：

```text
type  = ALL
key   = NULL
Extra = Using filesort
```

本次讨论中的原因是：

```text
按 idx_salary 顺序扫描
    ↓
为了 SELECT * 还需要不断回表
```

对于只有几行的小表，优化器可能认为：

```text
全表扫描 + 排序
```

成本更低。

因此：

> 索引存在不代表优化器一定会使用。

---

### 11.3 改成覆盖查询后利用索引

```sql
SELECT salary
FROM employee
ORDER BY salary;
```

实际：

```text
type          = index
possible_keys = NULL
key           = idx_salary
Extra         = Using index
```

此时：

```text
idx_salary 本身按 salary 有序
        ↓
顺序扫描即可满足 ORDER BY
        ↓
SELECT 只需要 salary
        ↓
索引本身覆盖查询
```

于是：

```text
不用 filesort
不用回表
```

---

## 12. 联合索引与 ORDER BY

索引：

```text
idx_dept_age(dept, age)
```

---

### 12.1 第一列等值固定后，第二列可用于排序

查询：

```sql
SELECT *
FROM employee
WHERE dept = 'Sales'
ORDER BY age;
```

结果：

```text
type     = ref
key      = idx_dept_age
key_len  = 122
rows     = 2
filtered = 100
Extra    = NULL
```

这里：

```text
dept = 'Sales'
```

固定了联合索引第一列。

在 `Sales` 这一段中：

```text
Sales, 25
Sales, 28
...
```

`age` 天然有序，因此：

```text
dept → 用于定位 Sales 范围
age  → 用于提供结果顺序
```

无需 `Using filesort`。

---

### 12.2 第一列是范围时，第二列不再全局有序

查询：

```sql
SELECT *
FROM employee
WHERE dept > 'Accounting'
ORDER BY age;
```

实际：

```text
type     = range
key      = idx_dept_age
key_len  = 122
rows     = 4
filtered = 100
Extra    = Using index condition; Using filesort
```

联合索引范围内可能是：

```text
Sales, 25
Sales, 28
Tech,  24
Tech,  32
```

单看 `age`：

```text
25, 28, 24, 32
```

不是全局有序。

所以即使 `age` 是联合索引第二列，也不能直接满足：

```sql
ORDER BY age
```

需要 `Using filesort`。

#### 重要直觉

对于：

```text
INDEX(a, b)
```

如果：

```text
a = 固定值
```

则该固定范围内 `b` 可以保持索引顺序。

如果：

```text
a > ...
```

涉及多个 `a` 值，那么单独看 `b` 通常不再是全局有序。

---

### 12.3 按完整联合索引顺序排序

查询：

```sql
SELECT *
FROM employee
WHERE dept > 'Accounting'
ORDER BY dept, age;
```

实际：

```text
type  = range
key   = idx_dept_age
Extra = Using index condition
```

没有：

```text
Using filesort
```

因为扫描出来的数据本来就按：

```text
(dept, age)
```

排列，正好满足排序要求。

---

## 13. 联合索引的正向与反向扫描

索引：

```text
(dept ASC, age ASC)
```

本次实验得出的规律：

```text
ORDER BY dept ASC,  age ASC
→ 可以正向扫描

ORDER BY dept DESC, age DESC
→ 可以整体反向扫描

ORDER BY dept ASC,  age DESC
→ 单纯正扫、反扫都不能直接满足

ORDER BY dept DESC, age ASC
→ 同理不能直接满足
```

实验：

```sql
SELECT *
FROM employee FORCE INDEX (idx_dept_age)
ORDER BY dept DESC, age DESC;
```

结果：

```text
type = index
key  = idx_dept_age
Extra = Backward index scan
```

没有 `Using filesort`。

而：

```sql
SELECT *
FROM employee FORCE INDEX (idx_dept_age)
ORDER BY dept ASC, age DESC;
```

实际结果仍然是：

```text
type = ALL
key  = NULL
Extra = Using filesort
```

---

### 13.1 为什么不能“每个 dept 分段反向扫 age”？

曾提出一个很有价值的问题：

> 联合索引是不是只能整段正向 / 反向扫描？能不能先处理一个 `dept`，在这个小段里反向扫描 `age`，再去下一个 `dept`？

从算法上可以想象这种行为，但本次讨论中形成的理解是：

> 那已经不是一次连续的 B+Tree 顺序扫描了。

对于：

```text
(dept ASC, age ASC)
```

连续正向遍历得到：

```text
dept ASC, age ASC
```

连续反向遍历得到：

```text
dept DESC, age DESC
```

而：

```text
dept ASC, age DESC
```

需要：

```text
dept 大方向向前
但每进入一个 dept 分组
age 又反向
```

这不能通过一次连续正向或反向遍历直接得到。

因此通常需要额外排序。

---

### 13.2 联合索引当然可以只扫描局部范围

另一个容易混淆的问题：

> 联合索引是不是只能一扫全部，不能只扫一部分？

答案是否定的。

例如：

```sql
WHERE dept = 'Sales'
```

只扫 `Sales` 这一段。

```sql
WHERE dept > 'Sales'
```

只扫对应范围。

所以：

```text
type = index
```

才表示全索引扫描；

而：

```text
ref
range
```

都可以只访问联合索引的一部分。

“局部扫描”和“混合排序方向”是两个不同问题。

---

### 13.3 第一列固定后可以在局部范围反向扫描

查询：

```sql
SELECT *
FROM employee
WHERE dept = 'Sales'
ORDER BY age DESC;
```

本次实际实验符合预期：

```text
dept = 'Sales'
```

先固定到联合索引的一小段，再在这段内对 `age` 反向扫描即可，无需额外排序。

---

## 14. `key_len` 在本次实验中的观察

本次没有深入计算 `key_len` 的字节组成，但通过实验用它判断联合索引参与程度。

例如：

```sql
WHERE dept = 'Sales'
ORDER BY age;
```

使用：

```text
idx_dept_age(dept, age)
```

时：

```text
key_len = 122
```

说明用于索引访问范围的主要是 `dept`。

而综合题：

```sql
SELECT dept, age
FROM employee
WHERE dept = 'Sales'
  AND age > 26
ORDER BY age DESC;
```

得到：

```text
key_len = 126
```

说明这次 `age` 也参与了联合索引范围访问。

该综合题完整结果：

```text
type     = range
key      = idx_dept_age
key_len  = 126
rows     = 1
filtered = 100
Extra    = Using where; Backward index scan; Using index
```

可以理解为：

```text
在 (dept, age) 中定位：
Sales 且 age > 26 的范围
        ↓
反向扫描
        ↓
直接满足 age DESC
        ↓
SELECT 只需要 dept、age
        ↓
覆盖索引，不回表
```

---

## 15. JOIN 的 EXPLAIN 为什么一张表一行

最初的疑问：

> JOIN 最终不是得到一个联表结果吗？为什么 EXPLAIN 有两行？预期似乎应该看到“联表消耗”和“查询联表的消耗”。

本次形成的核心理解：

> 传统 EXPLAIN 更像是在描述“为了完成 JOIN，MySQL 分别如何访问每张表”。

所以两张表 JOIN 通常会看到两行。

实验：

```sql
SELECT e.name, d.dept_id
FROM employee e
JOIN department d
    ON e.dept = d.dept_name;
```

实际顺序：

```text
d:
type = index
key  = dept_name
rows = 3
Extra = Using index

e:
type = ref
key  = idx_dept_age
ref  = d.dept_name
rows = 1
```

可以理解为：

```text
扫描 department
    ↓
拿到一个 dept_name
    ↓
用它去 employee 索引中查匹配记录
    ↓
拼接结果
    ↓
继续 department 下一行
```

JOIN 不是：

```text
先凭空生成一张完整大联表
        ↓
再统一查询
```

而是组织对各张表的访问并逐步匹配。

---

### 15.1 JOIN 中表的实际访问顺序可以被优化器调整

SQL 写的是：

```text
employee e
JOIN department d
```

但实际 EXPLAIN 第一行可能是：

```text
d
```

第二行才是：

```text
e
```

说明：

> SQL 中表的书写顺序不一定等于优化器真正的访问顺序。

本次小表中，优化器选择先扫只有 3 行的 `department`，再用 `d.dept_name` 去 `employee` 做索引查询。

---

### 15.2 JOIN 中的 `ref` 列

这是本次特别容易和 `type = ref` 混淆的地方。

例如：

```text
type = ref
key  = idx_dept_age
ref  = d.dept_name
```

可以连起来读：

> 使用 `idx_dept_age`，拿当前 `d.dept_name` 的值做等值索引查询。

其中：

```text
type = ref
```

描述访问方式；

而：

```text
ref = d.dept_name
```

表示“拿什么值去匹配这个索引”。

---

### 15.3 JOIN 的 `rows` 不能简单相加

如果执行计划：

```text
d rows = 3
e rows = 1
```

不能简单理解成：

```text
3 + 1 = 4
```

第二行 `rows = 1` 更接近：

> 对前面表的一条记录，预计从当前表匹配约 1 行。

因此粗略理解执行过程更像：

```text
扫描 d 的 3 条
+
对每条 d 记录去 e 做一次索引查询
```

---

## 16. `FORCE INDEX` 在实验中的作用与边界

本次用 `FORCE INDEX` 主要是为了控制变量、观察特定索引方案，不代表实际开发中应该随意强制索引。

例如：

```sql
SELECT *
FROM employee FORCE INDEX(idx_dept_age)
WHERE dept = 'Sales'
  AND age > 26;
```

成功强制联合索引后，看到了：

```text
type = range
```

以及：

```text
Using index condition
```

另一个实验：

```sql
SELECT *
FROM employee FORCE INDEX(idx_dept_age)
ORDER BY dept ASC, age DESC;
```

最终仍然：

```text
type = ALL
key  = NULL
Extra = Using filesort
```

本次讨论中的理解是：

> `FORCE INDEX` 不是“不管任何情况都必须扫描这个索引”。

如果索引本身无法直接满足当前排序，而查询又没有其他地方需要它来定位数据，那么“扫索引 + 回表 + 仍然 filesort”没有明显意义，优化器仍可能选择全表扫描加排序。

---

## 17. 优化器是做整体成本选择，而不是套单一规则

本次多个实验都体现了这一点。

---

### 17.1 有索引，不代表一定使用

```sql
SELECT *
FROM employee
ORDER BY salary;
```

即使存在：

```text
idx_salary(salary)
```

在只有几行的小表中，优化器仍可能：

```text
ALL + Using filesort
```

而不是：

```text
index scan + 回表
```

因为它会考虑整体成本。

---

### 17.2 联合索引更精确，也不代表一定选它

查询：

```sql
WHERE dept = 'Sales'
  AND age > 26
```

同时有：

```text
idx_dept(dept)
idx_dept_age(dept, age)
```

实际优化器曾选择：

```text
key = idx_dept
```

而不是联合索引。

`possible_keys` 中两个索引都存在：

```text
idx_dept_age, idx_dept
```

说明 MySQL 知道联合索引可用，但小数据下认为单列索引成本也足够低。

通过 `FORCE INDEX(idx_dept_age)` 才观察到了联合索引方案。

---

### 17.3 WHERE 最精准的索引，不一定是总体最优

综合题：

```sql
SELECT dept, COUNT(*) AS cnt
FROM employee
WHERE age > 26
GROUP BY dept
ORDER BY dept DESC;
```

直觉方案：

```text
idx_age
→ 先用 age > 26 做 range
→ 再 GROUP BY dept
→ 再 ORDER BY dept DESC
```

但实际执行计划选择：

```text
type     = index
key      = idx_dept_age
rows     = 6
filtered = 50
Extra    = Using where; Backward index scan; Using index
```

为什么？

因为：

```text
idx_age
→ WHERE 很精准
→ 但 GROUP BY / ORDER BY 需要后续处理

idx_dept_age
→ WHERE 无法直接缩成 age 范围，需要全索引扫描
→ 但 dept 天然适合 GROUP BY
→ 反向扫描天然满足 ORDER BY dept DESC
→ 查询又被索引覆盖
```

优化器最终选择了后者。

因此本次学习形成的一个重要直觉：

> 不要只问“WHERE 最适合哪个索引”，而要看整条 SQL 中过滤、分组、排序、覆盖、回表等总体成本。

---

## 18. 综合实验复盘

### 18.1 联合索引 + range + DESC + 覆盖索引

SQL：

```sql
SELECT dept, age
FROM employee
WHERE dept = 'Sales'
  AND age > 26
ORDER BY age DESC;
```

索引：

```text
idx_dept_age(dept, age)
```

实际：

```text
type     = range
key      = idx_dept_age
key_len  = 126
rows     = 1
filtered = 100
Extra    = Using where; Backward index scan; Using index
```

分析：

```text
dept='Sales'
→ 固定联合索引第一列

age>26
→ 第二列参与范围扫描

ORDER BY age DESC
→ 在 Sales 这一局部范围内反向扫描即可

SELECT dept, age
→ 两列都在联合索引中
→ 覆盖索引
```

这道题中曾错误预测：

```text
Using filesort
```

修正后的理解是：

> 第一列等值固定以后，第二列在该局部范围内仍然有序，可以正向或反向扫描，因此不一定需要 filesort。

---

### 18.2 过滤、分组、排序之间的索引权衡

SQL：

```sql
SELECT dept, COUNT(*) AS cnt
FROM employee
WHERE age > 26
GROUP BY dept
ORDER BY dept DESC;
```

实际：

```text
type     = index
key      = idx_dept_age
rows     = 6
filtered = 50.00
Extra    = Using where; Backward index scan; Using index
```

关键点：

```text
type = index
→ 全扫描 idx_dept_age

Using where
→ 判断 age > 26

Backward index scan
→ 反向按 dept 扫描

Using index
→ 查询被联合索引覆盖
```

没有：

```text
Using temporary
Using filesort
```

说明联合索引顺序直接帮助了 `GROUP BY dept` 与 `ORDER BY dept DESC`。

---

### 18.3 WHERE + ORDER BY + 回表

SQL：

```sql
SELECT dept, age
FROM employee
WHERE dept = 'Sales'
ORDER BY salary;
```

候选索引：

```text
idx_dept
idx_dept_age
idx_dept_salary
```

实际：

```text
type     = ref
key      = idx_dept_salary
key_len  = 122
rows     = 2
filtered = 100
Extra    = NULL
```

分析：

```text
dept='Sales'
→ 使用 idx_dept_salary 第一列做 ref 等值访问

salary
→ 没有用于缩小 WHERE 范围
→ 但在 Sales 范围内天然有序
→ 满足 ORDER BY salary

SELECT age
→ age 不在 idx_dept_salary 中
→ 需要回表
```

因此：

```text
没有 Using filesort
没有 Using index
Extra = NULL
```

这里再次说明：

> 联合索引中的某一列即使没有参与“定位范围”，仍然可以参与排序。

---

## 19. 本次学习中最容易混淆的点

### 19.1 `type = index` vs `Using index`

错误直觉：

```text
index 都表示用了索引
```

修正：

```text
type = index
→ 全索引扫描

Using index
→ 覆盖索引，不回表
```

---

### 19.2 `Using index condition` vs `Using index`

```text
Using index condition
→ ICP
→ 利用索引提前过滤，核心价值是减少回表

Using index
→ 覆盖索引
→ 查询本身不需要回表
```

---

### 19.3 `Using where` 不等于没走索引

错误理解：

```text
Using where
→ WHERE 没利用索引
```

修正：

```text
Using where
→ MySQL 仍需要应用 WHERE 条件判断
```

是否利用索引应该看：

```text
type
key
key_len
```

---

### 19.4 `possible_keys = NULL` 不等于不会用索引

实际出现：

```text
possible_keys = NULL
key           = idx_salary
```

因此最终是否使用索引看 `key`。

---

### 19.5 `Extra = NULL` 不等于没做事情

例如主键查询：

```text
type  = const
key   = PRIMARY
Extra = NULL
```

仍然是非常明确、高效的主键唯一定位。

---

### 19.6 有多个单列索引，不等于有联合索引

```text
INDEX(dept)
INDEX(salary)
```

不能替代：

```text
INDEX(dept, salary)
```

联合索引维护的是联合排序关系。

---

### 19.7 范围条件之后的列与排序能力不是同一个问题

查询：

```sql
WHERE dept > 'Accounting'
ORDER BY dept, age;
```

虽然第一列 `dept` 已经是范围条件，但扫描出来的数据仍然保持 `(dept, age)` 的整体索引顺序，因此可以避免 `filesort`。

所以：

> “某列能不能继续用于索引定位”和“扫描结果能不能直接满足 ORDER BY”是两个不同问题。

---

### 19.8 联合索引可以局部扫描，但混合方向排序不一定能直接利用

```text
WHERE dept='Sales'
```

当然可以只扫描 Sales 局部范围。

但：

```text
ORDER BY dept ASC, age DESC
```

无法通过 `(dept ASC, age ASC)` 的一次连续正向或反向扫描得到。

不要把：

```text
局部扫描
```

和：

```text
混合排序方向
```

混为一谈。

---

## 20. 当前阶段的 EXPLAIN 阅读框架

看到一份执行计划时，可以按下面顺序快速判断：

```text
1. table
   当前这一行是在访问哪张表？

2. type
   是 ALL / index / range / ref / eq_ref / const 中哪种访问方式？

3. possible_keys
   优化器认为哪些索引可能有价值？

4. key
   最终实际用了哪个索引？

5. key_len
   联合索引实际参与访问范围的大致程度是否发生变化？

6. ref
   等值查询时，拿什么值去匹配索引？
   尤其 JOIN 中可能来自前一张表。

7. rows
   预计需要检查多少行？

8. filtered
   候选记录中预计有多少比例能继续保留？

9. Extra
   是否出现：
   - Using where
   - Using index
   - Using index condition
   - Using filesort
   - Using temporary
   - Backward index scan
```

最后不要只盯一个字段，而是把整条 SQL 联合起来判断：

```text
WHERE
+
JOIN
+
GROUP BY
+
ORDER BY
+
SELECT 字段
+
是否覆盖
+
是否回表
```

优化器选择的是整条执行方案，而不是机械地优先某一个局部规则。
