# AI 提示词库

这里收录了我在使用大模型时整理的提示词，涵盖 PPT 学习、考前复习、笔记整理和提示词编写。可以直接复制，也可以按实际需求调整。

!!! info "使用方法"
    选择合适的模板，通过代码块右上角按钮复制。学习类模板需要提供 PPT 或完整学习会话；Prompt Writer 需要提供任务背景、目标和期望输出。

| 模板 | 适用场景 | 输出方式 |
| --- | --- | --- |
| [PPT 逐页精讲](#ppt-deep-dive) | 首次学习、深入理解课程内容 | 分批讲解，通常每次 3～5 页 |
| [PPT 期末速通](#ppt-exam-review) | 复习、预习、考前冲刺 | 按模块讲解，通过练习反馈调整进度 |
| [整理对话笔记](#conversation-notes) | 将完整学习会话沉淀为笔记 | 生成独立的 Markdown 笔记文件 |
| [Prompt Writer](#prompt-writer) | 编写新提示词、改进已有提示词 | 根据任务背景、目标和期望输出设计 Prompt |

---

## PPT 逐页精讲 { #ppt-deep-dive }

适合第一次系统学习课程内容。重点是理解知识的前后逻辑，以及公式、图表、例题和练习题，而不是快速浏览。

**适合：** 时间较充足、希望打牢基础、需要逐页理解。

### 提示词

```text
# PPT 逐页精讲

我上传了一份课程 PPT。请你像一位有教学经验的大学老师一样，带我系统学习其中的知识。我的目标是真正理解知识，包括核心概念、原理、公式、图表、例题，以及知识点之间的联系。我希望你的讲解能带我循序渐进地建立心智模型，而不是简单的复述或概括 PPT。

## 一、整体导读

正式讲解前，请先通览整份 PPT，帮助我建立对课程内容的整体认识：

- **知识主线：** 这份 PPT 主要讲什么，试图解决哪些问题？
- **内容结构：** 可以分成哪些知识模块？它们之间有什么联系？
- **学习重点：** 哪些内容是理解整份 PPT 的关键，哪些地方可能存在理解难点或常见误区？
- **练习安排：** PPT 中有哪些值得关注的例题、练习题，它们主要对应哪些知识点？

导读应简明扼要，帮助我建立学习框架即可，不必提前详细讲解全部知识。

## 二、逐页讲解

原则上按照 PPT 的页码顺序推进，确保知识学习的连续性。对于内容紧密相关的页面，可以联系起来讲解，但应让我清楚当前对应的页码和知识范围。

讲解时，重点关注以下问题：

1. **核心内容：** 这一页真正需要理解或掌握的是什么？
2. **背景与动机：** 为什么要介绍这个概念、方法或技术？它解决什么问题？
3. **理解过程：** 如何从直观认识逐步理解其正式定义、原理或推导？
4. **知识联系：** 它与前面学过的内容有什么关系？在后续知识中又有什么作用？
5. **学习重点：** 哪些地方容易混淆或出错，哪些内容可能用于作业、实验或考试？

这些是讲解时推荐的关注方向，**不是要求每页都依次回答的固定问题**。请根据页面实际内容决定讲解重点和组织方式。

不同页面应有不同的讲解深度：

- 目录、过渡、背景介绍或简单结论页，可以简要说明其作用。
- 重点概念、复杂原理、公式推导、算法流程等内容，应适当展开，确保能够理解。
- 对于相互关联的知识点，可以适当回顾或提前建立联系，避免孤立地介绍概念。

根据 PPT 的内容灵活调整，不要为了逐页而逐页，也不要为了讲得详细而无意义地扩展。

## 三、针对不同内容的讲解

根据 PPT 的内容类型，选择合适的解释方式。

**1. 概念与原理**

对于重要概念，尽量先建立直观认识，再解释正式定义和核心机制。说明它为什么存在、解决什么问题，以及与相关概念的区别。对于抽象或容易混淆的内容，可以通过具体例子、类比或对比帮助理解，但不要让类比替代真实原理。

**2. 公式与推导**

遇到重要公式时，重点解释：

- 公式用于解决什么问题，为什么需要它；
- 关键符号、变量及其含义；
- 公式背后的直观思想和计算逻辑；
- 如何使用公式，以及实际计算时需要注意什么。

如果推导过程对理解很重要，应适当展开；如果重点在于理解和应用，也不必强行进行复杂推导。

**3. 图表与示意图**

对于结构图、流程图、曲线图等，不要仅仅描述图上有什么，还应解释图表整体表达的含义、关键部分之间的关系，以及它如何帮助理解当前知识点。复杂图表可以按照合理的阅读顺序逐步拆解，帮助我理解其中的逻辑。

**4. 代码、算法与流程**

对于代码或伪代码，先说明整体功能及输入、输出，再围绕核心逻辑解释关键步骤。重点关注为什么这样实现、哪些步骤是理解算法的关键，以及容易出现的错误。

涉及重要的算法性质、复杂度或适用条件时，也应适当说明。不需要机械地逐行解释所有代码，除非具体内容确实需要。

**5. 例题与练习题**

不要跳过 PPT 自带的例题、练习题和课堂思考题。遇到这些内容时，应先明确涉及的知识点，再分析解题思路，逐步完成解答，并总结其中具有普遍意义的方法和易错点。

对于适合互动的练习，可以先让我尝试，再根据我的回答讲解。对于讲解型例题，则可以直接完整分析。

习题的重点不在答案，而是让我理解这类问题应该如何思考和解决。

## 四、学习互动与阶段总结

希望整个过程是一种自然的互动式教学，而不是单方面连续输出大量内容。每一块知识点（一页或者几页 PPT 串联成一个完整的知识点）讲解结束时，原则上用一两句话归纳最值得记住的内容。对于重要或容易混淆的知识，可以补充一个简短的自测问题。根据教学需要决定是否直接提供参考答案，或等待我作答后再进行反馈。

并非所有页都安排总结、测试。例如目录页、过渡页、简单说明页，以及已经包含练习的页面，可以省略额外的总结或提问。对于关键难点，可以适当停下来检查我的理解。根据我的回答或追问判断是否需要补充解释、换一种讲法，或者继续后面的内容。

如果我已经表现出理解，不必反复确认；如果存在明显误解，应帮助我找到理解偏差，而不仅仅给出正确结论。

## 五、内容依据与讲解风格

以 PPT 的实际内容为主要依据，尽量保持原有知识体系和学习顺序。

如果 PPT 省略了必要的背景、解释或中间推导，可以适当补充，帮助我理解。但应能够区分哪些内容来自 PPT，哪些是额外的教学补充。

如果某些图片、公式或文字无法准确辨认，请明确说明，不要凭空猜测。

讲解应清晰、自然、有逻辑，避免机械罗列标题、重复结论或使用固定模板。根据内容的实际复杂度决定篇幅，既不要把简单内容讲得过于冗长，也不要因为追求简洁而省略理解关键知识所必需的解释。

## 六、输出节奏

如果 PPT 内容较多，请分批进行，不要一次性讲完整份。

通常每次讲解 **3～5 页**，但可以根据内容密度和知识关联适当调整。复杂内容可以少讲几页，简单内容可以适当合并。

第一次回复请先完成整体导读，然后开始前 3～5 页的讲解。

每批讲解结束后暂停，等待我提出问题或说“继续”，再推进后续内容。
```

## PPT 期末速通 { #ppt-exam-review }

适合预习、课程复习或考前冲刺。按知识模块和重要程度推进，优先使用 PPT 自带题目，并根据答题反馈调整学习进度。

**适合：** 时间有限、目标明确、需要优先掌握高频考点。

### 提示词

```text
# PPT 期末速通

我上传了一份课程 PPT，希望你帮助我高效率地学习和复习其中的内容，为课程考试做准备。

我的情况是：部分内容可能没有系统学过，也可能已经有所了解。我希望用较短时间掌握课程的知识主线、核心概念、重要原理和可能考点，并通过练习检验理解程度。

请具备一定的时间观念，逐页精讲对我们太过笨重，而快速概括无法取得学习效果。请以**快速理解知识、识别重点、完成练习、根据反馈调整学习进度**为主要目标，在学习效率和理解深度之间取得平衡。

## 一、整体导读与复习规划

正式学习前，请先通览整份 PPT，帮助我建立整体认识：

- **知识主线：** 这份 PPT 主要讲什么，涉及哪些核心问题？
- **模块划分：** 可以分成哪些知识模块？各模块解决什么问题，彼此之间有什么联系？
- **复习重点：** 哪些内容最值得投入时间，哪些可以快速理解或略读？
- **考点分布：** 哪些知识可能成为考试题目，PPT 自带的例题、练习题主要分布在哪里？

根据知识的重要程度和可能的考查要求，将内容大致分为三个等级：

1. **必须掌握：** 核心概念、重要原理、关键公式和方法，以及很可能用于考试、作业或实验的知识。
2. **理解即可：** 需要理解基本思想、作用和主要结论，但通常不必深入研究全部细节。
3. **快速略读：** 主要用于介绍背景、提供补充信息，或对当前复习目标价值较低的内容。

分级是为了合理分配学习时间，而不是将所有知识机械归类。对于重要程度存在争议的内容，可以说明判断依据。如果缺少影响复习方向的关键信息，可以向我询问；其他情况下应优先根据现有资料作出判断。

请优先依据 PPT 本身的内容、强调方式、练习题和知识依赖关系判断重点。必要时可以结合课程常见的考查方式进行推测，但应区分**PPT 明确强调的重点**与**根据课程内容推测的考点**，不要将推测当成老师确定的考试范围。

整体导读应简明扼要，不必在开始阶段就展开全部考点和细节。

## 二、按知识模块高效率讲解

原则上按照知识模块推进，而不是机械地逐页复述 PPT。可以将相关页面组合讲解，但应保留对应的页码或页码范围，方便我回到原始资料复习。

每个模块应重点帮助我理解：

1. **核心问题：** 这个模块主要讲什么，为什么需要学习它，解决什么问题？
2. **知识内容：** 需要掌握哪些概念、原理、公式、方法或重要结论？
3. **理解逻辑：** 这些知识为什么成立，关键机制是什么，如何从直观认识过渡到正式理解？
4. **知识联系：** 它与其他模块有什么关系，哪些知识需要联系起来理解？
5. **考查方向：** 哪些地方可能出题，常见的考查方式是什么，容易混淆或出错的地方在哪里？

这些是讲解时推荐的关注方向，**不需要每个模块都机械地按照五个问题展开**。请根据内容实际特点决定讲解结构和深度。

以备考效率为优先：

- 对必须掌握的内容，应讲清核心思想、关键机制及应用方法，避免只给出定义和结论。
- 对理解即可的内容，重点说明基本思想、用途和关键特点，不必过度深入。
- 对快速略读的内容，可以简要介绍，必要时直接说明其背景作用。
- 如果某个看似简单的知识是理解后续内容的基础，也应适当讲清楚。

对于我尚未学习过的内容，需要提供必要的解释，不能因为当前在复习就默认我已经掌握基础。

讲解应先建立知识主线，再根据重要程度深入细节。不要为了压缩时间而省略理解核心知识所必需的解释，也不要为了完整而进行大量低价值扩展。

## 三、重点内容与考点分析

根据 PPT 中的实际内容，灵活处理不同类型的知识。

**1. 概念、定义与分类**

- 对于重要概念，说明其含义、作用和关键特征。
- 特别关注容易混淆的概念、不同方法之间的区别，以及有明确分类、特点、优缺点或适用条件的知识。
- 在必要时，可以补充对比或例子，帮助我快速理解和记忆。

**2. 公式与计算**

遇到重要公式时，重点解释：

- 公式用于解决什么问题；
- 关键符号、变量及其含义；
- 公式背后的直观思想和计算逻辑；
- 如何使用公式，必要时通过例题演示；
- 可能出现的计算题型和常见错误。

对于考试或理解中必要的推导，应适当展开；如果只需要掌握应用方法，不必强行深入复杂的数学推导。

**3. 图表与示意图**

对于结构图、流程图、曲线图和其他重要图表，应解释其整体含义、关键部分及相互关系。如果图表可能用于简答题、分析题或识图题，还应帮助我理解如何根据图表说明相关原理。注意，重在说明图表想表达的知识，而不是停留在表面的描述。

**4. 算法、流程与代码**

对于算法、流程或代码，优先讲清：

- 解决的问题，以及主要输入和输出；
- 核心步骤与整体工作流程；
- 关键步骤为什么这样设计；
- 重要的算法性质、复杂度、适用条件或局限性；
- 可能涉及的分析题、计算题或算法理解题。

讲解深度应与知识的重要程度相匹配。重点是理解算法思想和关键逻辑，而不是机械地逐行解释代码。

**5. 考点提取**

在模块学习过程中，结合相关内容指出值得关注的考点，包括：

- 对应的 PPT 页面或知识范围；
- 需要掌握到什么程度；
- 可能的题型和考查方式；
- 容易出现的误解、错误或遗漏。

特别关注 PPT 反复强调的知识，以及其中的定义、分类、公式、算法、图表、例题和练习题。反复是信号，代表这块内容可能相对重要，但重要程度同时也应关注知识点自身的价值。结合知识点实际作用、相关练习和知识依赖关系综合判断。

不必将所有知识都强行整理成考点表，也不需要对每个概念猜测一种考试题型。只有对复习有实际帮助时，才展开具体的考点分析。

## 四、练习题与知识巩固

练习是学习过程的重要组成部分。请优先利用 PPT 自带的例题、练习题、课堂思考题和实验题，在此基础上根据需要补充练习。

**1. 优先处理 PPT 自带题目**

不要直接跳过 PPT 中具有学习或复习价值的题目，也不要在尚未处理相关原题时，就大量生成新的练习。

遇到题目时，应明确它考查的知识点，并根据题目类型选择合适的教学方式：

- **讲解型例题：** 可以直接分析解题思路，逐步完成解答，并总结关键方法。
- **适合独立完成的练习：** 优先让我尝试作答，再根据我的回答进行讲解。
- **难度较高的题目：** 可以先提供必要的思路或提示，帮助我找到解题方向。

无论采用哪种方式，都应让我理解题目为什么这样解，以及同类问题通常应该如何思考。

对于明显重复、考查内容完全相同的题目，可以结合实际掌握情况适当合并处理，但不要因此遗漏新的知识点或重要题型。

**2. 必要时补充练习**

如果 PPT 自带题目不足，或某些重要考点缺少对应练习，可以补充少量有针对性的题目。

根据需要选择合适的练习形式：

- **基础题：** 选择、填空、判断等，检查概念和基础知识。
- **理解题：** 简答、概念辨析等，检查是否真正理解原理。
- **应用题：** 计算、分析、算法、流程或图表解释，检查知识运用能力。
- **综合题：** 联系多个知识点，训练综合分析与解决问题的能力。

补充练习应围绕 PPT 的核心知识及可能考查方式，不要脱离课程内容随意扩展。

不需要每个模块都覆盖所有题型或难度层级。练习数量应根据知识复杂度和我的实际表现调整，避免重复训练已经掌握的内容。

**3. 答题反馈**

当我完成练习后，请根据实际答案进行分析，而不仅仅判断对错。

重点说明：

- 哪些部分正确，哪些地方不完整或存在错误；
- 错误是来自概念理解、推理过程、计算方法，还是知识运用；
- 正确的思路、答案或关键步骤是什么；
- 以后遇到类似题目，应重点注意什么。

如果我的答案基本正确，只存在少量遗漏，可以直接指出并继续；如果暴露了明显的知识漏洞，应针对问题补充讲解。

如果我明确要求直接给出答案，则提供参考答案和必要的解析，不必坚持让我先作答。

## 五、学习流程与进度调整

请按照**「讲解 → 练习 → 反馈 → 调整进度」**的方式推进学习，但不必机械地把每个模块变成完全相同的固定流程。

一般情况下：

1. 先讲解当前模块的核心知识，明确需要掌握的重点。
2. 优先处理 PPT 中相关的例题和练习题。
3. 如果缺少必要练习，再补充少量有针对性的题目。
4. 对于需要我独立完成的练习，给出题目后暂停，等待我的回答。
5. 根据答题表现和反馈，决定继续、补讲还是强化训练。

请根据实际情况灵活调整：

- 如果我掌握得较好，可以加快节奏，进入后续模块。
- 如果只是存在小错误，指出关键问题后即可继续。
- 如果出现明显理解偏差，应解释错误原因，必要时换一种方式讲解。
- 如果某类题目反复出错，可以补充 1～3 道同类题进行针对性训练。
- 如果我对某个问题特别感兴趣，或明确希望深入理解，可以适当暂时偏离速通节奏。

不要连续讲解大量模块而缺少必要的理解检查，也不要为了互动而频繁打断已经顺畅的学习过程。**学习进度应由知识的重要程度和我的实际掌握情况共同决定，而不是严格执行预先设定的讲解或练习数量。**

## 六、内容依据、讲解风格与输出节奏

以 PPT 的实际内容为主要依据，保持知识内容和重要结论的准确性。对于 PPT 没有详细说明、但理解或考试需要的背景知识，可以适当补充，并区分原始内容与额外解释。如果图片、公式或文字无法准确辨认，请明确说明，不要凭空猜测。

讲解应清晰、自然、有逻辑，尽量使用具体的解释帮助理解，避免只罗列概念、考点和答案。

**首次回复：**

1. 简要完成整份 PPT 的整体导读；
2. 给出知识模块划分、重要程度和主要考点的概览；
3. 开始第一个模块的高效率讲解；
4. 优先处理该模块相关的 PPT 自带例题或练习；
5. 如果没有合适的原题且确有必要，可以补充约 1～4 道练习，数量根据内容调整，复杂模块，可以适当增加，简单模块，可以适当减少。

对于需要我作答的题目，请在给出题目后暂停，等待我的回答。

后续根据答题情况和我的反馈，继续下一模块、补充讲解或进行针对性练习。

不要一次性讲完整份 PPT，也不要在首次回复中输出过于庞大的考点清单或复习计划。始终把实际学习和知识掌握放在首位。
```

## 整理对话学习笔记 { #conversation-notes }

将完整的学习会话整理为可独立阅读的 Markdown 笔记。只整理会话实际支持的知识，保留有复习价值的误解、纠正、代码和实验，不额外补充会话外的知识。

**适合：** 完成一轮问答学习后，沉淀长期可复习的资料。

### 提示词

```text
# 整理对话学习笔记

请根据当前完整的学习会话，帮我整理一份适合长期保存和后续复习的 Markdown 学习笔记。

**这不是聊天摘要，也不是重新编写一份相关主题的教程。** 我希望你从学习过程中提炼真正有价值的知识，保留重要的概念、原理、推导、例子、误解和纠正，并按照知识之间的逻辑关系重新组织，使最终笔记能够脱离原始对话独立阅读。

整理的核心原则是：

**保留知识价值，而不是保留学习过程；删除冗余，而不是删除知识。**

## 一、筛选具有复习价值的内容

在整理之前，请先从整个会话中识别真正值得长期保留的知识。

重点关注以下内容：

- **核心知识：** 概念、定义、原理、机制、规则、公式、推导和使用方法。
- **理解过程中的重要发现：** 对某个知识点的深入解释、关键原因、不同角度的理解，以及有助于建立正确认识的例子。
- **知识辨析：** 容易混淆的概念、不同方法或写法的比较、适用条件、特殊情况和边界。
- **误解与纠正：** 我曾经出现的错误理解、不准确的判断，以及后续得到的纠正和解释。
- **技术实践：** 重要的代码、API、命令、配置、算法、实验结果及其背后的知识。
- **有价值的练习：** 能够体现关键方法、暴露理解漏洞，或值得以后重新练习的题目。

这些是值得关注的内容类型，不代表所有出现过的内容都必须保留。应根据其实际复习价值进行选择。

**判断标准：如果未来我只拿到这份笔记，完全不知道当时的聊天过程，这段信息是否仍然有助于我理解、回忆、辨析或应用知识？**

如果没有独立的复习价值，就不必保留。

## 二、区分学习过程与知识内容

学习会话中存在大量服务于当时教学的过程性信息，它们通常不应该进入最终笔记。

例如：

- 为了解我的基础而进行的前置询问。
- 关于讲解方式、深度、顺序和学习计划的讨论。
- “继续”“明白了”“换个例子”“先停一下”等流程性交流。
- 与知识无关的学习感受、寒暄和反馈。
- 为完成任务而进行的文件、环境、格式确认。
- 模型对接下来准备如何讲解的说明。
- 没有产生新知识的过渡内容或重复解释。

但不要仅凭信息的形式决定是否删除，而应判断它是否产生了独立的知识价值。

例如：

**学习过程：**

“你熟悉 JavaScript 吗？”

“那我用 JavaScript 来类比 Scala。”

这些只是教学方式的协商，通常不值得记录。

**有价值的知识：**

“Scala 的 val / var 与 JavaScript 的 const / let 有什么区别？”

如果会话围绕这个问题形成了明确的知识比较，就应该保留比较本身，而不是保留为什么选择这种讲解方式。

同样，如果我反复追问某个概念，并最终纠正了一个重要误解，应保留这个概念的关键解释、误区及正确理解，而不是记录我追问了多少次。

**最终笔记应体现学习过程中形成的知识，而不是描述学习过程发生了什么。**

## 三、保留误解、纠正与重要问题

不要只提取会话中的最终结论。学习过程中暴露出来的误解、疑问和理解偏差，往往同样具有复习价值。

当一个问题满足以下情况时，应考虑保留其知识意义：

- 暴露了容易混淆的概念或错误认识。
- 推动出了新的解释、原因或推导。
- 揭示了特殊情况、适用范围或边界条件。
- 产生了值得以后重新思考的问题。
- 经过讨论，使原有理解得到了重要修正。

对于有价值的误解，可以整理为「易错点」「常见误解」「概念辨析」等内容，重点说明：

1. 原来容易产生什么理解，以及问题在哪里。
2. 会话中最终形成了怎样的正确或更准确的理解。
3. 为什么容易混淆，以及如何区分。
4. 必要时保留会话中已有的关键例子。

例如，对话中可能出现：

“我还是分不清 map 和 flatMap。”

“能不能换一种方式解释？”

“现在我理解了。”

最终笔记不需要保留这些交流本身，而应该整理出 map 与 flatMap 的关键区别、造成混淆的原因，以及会话中帮助澄清问题的解释。

对于重要的疑问，也不必强行改写成普通陈述。如果问题本身非常适合作为复习时的思考题，可以保留问题形式，并整理会话中已经形成的解答。

不要把所有追问都写进笔记，也不要因为最终得到了正确答案，就把有复习价值的错误理解全部抹掉。

## 四、去除冗余，同时保留知识的完整性

**不要为了让笔记更短，而删除独立且有价值的知识。**

如果同一个知识点在会话中被多次讨论，应判断后续讨论是否增加了新的知识价值。

以下情况通常值得保留：

- 增加了新的原理解释或推导。
- 从不同角度澄清了一个容易误解的概念。
- 补充了具有独立价值的例子或对比。
- 引入了新的特殊情况、限制或边界。
- 通过错误分析揭示了此前没有理解的机制。
- 通过实验或实践形成了新的认识。

这些内容不应简单地因为属于同一个知识点就被合并丢失。

但是，如果多次解释只是换了一种表达，没有增加新的知识、原因、例子或区别，就没有必要保留所有版本。

应选择最适合长期复习的表达，并整合其他讨论中真正新增的信息。

例如，同一个概念先后经历了：

初步定义 → 直观解释 → 具体例子 → 发现误解 → 补充边界情况

最终可以将这些内容整理为一个连贯的知识小节，而不需要保存五段独立的聊天记录。

类似地，如果早期的临时说法已经被后续更准确的解释完全取代，可以采用后续解释；只有早期说法中的误区或差异仍具有学习价值时，才需要保留。

**完整性应以有效知识为单位，而不是以对话轮次或原始信息量为单位。**

## 五、代码、技术细节与实验

对于技术学习会话，请特别关注代码、API、语法、命令、配置、算法和实验，因为这些内容通常无法仅靠自然语言概括来替代。

### 1. 代码与技术细节

根据复习价值保留：

- 关键语法、API、参数及其作用。
- 核心算法逻辑和重要实现方法。
- 典型用法、执行时机和适用条件。
- 容易出错的写法及其原因。
- 不同实现方式之间的重要区别。
- 有助于理解机制的最小代码示例。
- 会话中实际讨论过的关键技术细节。

对于较长的代码，应优先保留与知识点直接相关的部分，不需要无意义地复制完整程序。

如果一段代码经过多次修改，可以保留最终的关键实现，以及能够说明问题的错误写法或修改前后的重要差异。不必机械记录每次修改。

但也不要为了压缩篇幅，将有复习价值的代码全部改写成几句自然语言。

对于 API 名称、类名、函数名、变量名、命令、文件名和技术术语，应尽量保持其原有含义和准确写法，不要随意翻译、重命名或修改。

### 2. 练习与实验

不是所有练习和实验都有长期保存价值。

优先保留：

- 用来验证某种原理或机制的实验。
- 实际结果与原先预测不同的实验。
- 揭示特殊情况、边界条件或错误理解的实验。
- 有代表性的代码、命令或计算练习。
- 以后值得重新完成的典型练习。

对于只用于检查环境、确认代码能够运行，或者没有带来新知识的重复测试，可以省略。

保留实验时，重点整理：

**实验目的 → 关键方法或代码 → 观察结果 → 得出的认识**

不必记录完整操作流水账。只有当某些步骤对理解实验结果或复现关键现象确实重要时，才需要保留。

如果讨论中只有预测或设想，没有实际执行和观察结果，应保留其原有的不确定性，不要写成已经验证的结论。

## 六、内容可信度与知识边界

本次整理严格采用 **closed-world（封闭知识范围）** 原则。

**只能以当前会话中实际出现并能够支持的内容为依据，不要搜索互联网，也不要使用会话之外的知识自行补充、纠错或扩展。**

尤其不要为了让笔记显得更加完整，而自行加入：

- 会话没有讨论过的定义、原理或推导。
- 新的例子、最佳实践或注意事项。
- 额外的技术背景或知识体系。
- 没有经过会话支持的推论和结论。
- 基于模型自身知识对原有讨论进行的额外纠错。

如果会话只讨论了一个概念的某个方面，就只整理这一部分，不需要补成完整教程。

对于会话中已经发生的纠正，应以讨论最终形成的理解为依据；对于仍然存在矛盾、疑问或不确定性的内容，不要擅自确定结论。

如果某个问题尚未解决、只形成了猜测，或者明确被暂时搁置，可以根据其后续学习价值，保留为「尚未解决的问题」或「待进一步验证的认识」。

需要区分会话中的事实、实验观察、解释、推测和未解决问题，不要将它们混为同一确定程度的结论。

整理的目的是忠实呈现**本次学习会话实际形成的知识**，而不是依据模型知道的更多内容重新编写教程。

如果无法访问完整会话，应明确说明实际可用的内容范围，不要假装已经分析了不可访问的部分。

## 七、笔记组织、篇幅与最终交付

### 1. 按照知识逻辑重新组织

最终笔记应该是一份正常的学习资料，而不是按时间顺序排列的对话摘要。

请按照知识之间的语义关系组织内容，将属于同一主题的概念、解释、推导、误区、例子和注意事项放在一起，即使它们原本出现在会话的不同位置。

对于存在明显依赖关系的知识，可以按照更适合阅读和复习的顺序排列，不必遵循原始聊天顺序。

章节划分应保持合理的粒度：

- 不要把大量不同知识笼统放入一个章节。
- 也不要将每个小问题都拆成独立章节。
- 一个章节或小节应围绕一组能够自然形成连贯解释的知识。

可以根据需要使用「核心概念」「关键机制」「概念辨析」「易错点」「示例」「实验」等小节，但不要机械套用固定模板。

没有对应内容时，不必为了结构完整而创建空泛的章节。

同样，不需要额外添加学习背景、会话时间线、学习过程回顾、学习感受等内容，除非其中确实包含值得复习的知识。

### 2. 根据知识量决定篇幅

不要预先限制笔记长度。

如果会话形成了大量独立且有价值的知识，可以整理为较长的笔记；如果实际知识较少，就不必为了篇幅而增加内容。

重点关注知识是否得到充分表达，而不是字数多少。

对于重要原理、机制、推导和例子，应保留理解所必需的细节。对于简单概念和重复信息，可以使用更简洁的表达。

不要把知识笔记压缩成只包含标题和结论的提纲，也不要因为追求完整而保留大量没有独立价值的信息。

### 3. 最终质量检查

在生成最终笔记前，请检查：

1. 是否遗漏了独立且有复习价值的知识、机制、例子或边界情况？
2. 是否保留了重要的误解、纠正及其背后的原因？
3. 是否正确合并重复内容，同时保留不同讨论带来的新增价值？
4. 是否混入了只服务于当时教学、缺乏独立知识价值的过程性信息？
5. 是否加入了会话没有支持的新知识，或将未确定的内容写成事实？
6. 章节结构是否自然，能否脱离原始对话独立阅读和复习？

可以用一个简单的问题判断某段内容是否值得保留：

**如果删除这一段，会不会损失一个独立的知识点、关键解释、重要例子、误解纠正或边界条件？**

如果不会，就倾向于合并或删除。

最终目标是：**知识完整、内容可信、结构自然、过程干净。**

### 4. 输出要求

请直接生成最终的 Markdown 学习笔记，并根据实际知识内容拟定合适的标题。

不要额外输出整理过程、内容筛选报告、笔记质量评价、删除内容清单或与笔记无关的学习建议。

不要直接将完整 Markdown 正文输出在聊天中。请将其写入独立的 `.md` 文件，并提供下载链接。

如果当前环境无法生成可下载文件，但能够写入实际文件，则返回真实存在的文件路径。不要虚构文件或下载链接。
```

## Prompt Writer { #prompt-writer }

将需求转化为适合大模型的 Prompt，根据任务特点确定需要提供的背景、约束和表达方式。

**适合：** 需要编写新提示词，或根据实际效果调整已有提示词。

### 提示词

```text
---

# Prompt Writer

A prompt's job is not to spell out every rule. The context window is a public good, so aim for the smallest set of high-signal tokens that maximize the likelihood of the output you want. The more rules you write, the more you box the output into the range of things you happened to think of. Assume the model is already very smart and only add context it doesn't already have — challenge every line: does this paragraph justify its token cost, or can I assume the model knows this?

## First, set the degrees of freedom

The most important decision is how much latitude to give the model: match the level of specificity to the task's fragility and variability. Picture the model exploring a path. On a narrow bridge with cliffs on both sides there is only one safe way forward, so give exact instructions and specific guardrails — this is low freedom, and it fits schemas, data formats, migrations, API calls, anything where a small error makes the output unusable. In an open field with no hazards many paths lead to success, so give general direction and trust the model to find the route — this is high freedom, and it fits grouping, generation, copywriting, subjective judgment, anything where several outputs are valid and quality is a judgment call.

Get this wrong and everything downstream is wrong. Write an open-field task with narrow-bridge language and the model collapses to the most generic result; write a narrow-bridge task with open-field language and it improvises where it must not.

|           | High freedom (open field)                            | Low freedom (narrow bridge)                      |
| --------- | ---------------------------------------------------- | ------------------------------------------------ |
| When      | Several valid outputs; quality is a judgment call    | One correct output; small errors break it        |
| Examples  | Grouping, generation, copywriting, subjective rating | Schemas, data formats, migrations, API calls     |
| How       | Goal + role + canonical examples                     | Exact steps + strict template                    |
| Trade-off | Trust the model's judgment, fewer rules              | Constrain with rules, leave no room to improvise |

Most real prompts mix both modes. An agent prompt leaves the approach open but locks the tool-call format; a generation task gives free rein on content but demands strict JSON out. Zone the prompt instead of picking one mode for the whole thing: narrow-bridge treatment for formats, schemas, and tool calls; open-field treatment for content and judgment. And calibrate to the model that will run the prompt — the weaker the model, the more everything shifts toward the narrow bridge.

## Find the right altitude

Within either mode, aim for the right altitude: specific enough to guide behavior, flexible enough to leave the model strong heuristics. Too low is hardcoding brittle logic — "if the title contains a colon, split on it and capitalize the second half." Too high is vague guidance with no concrete signal — "write good titles." The altitude that works sits between the two: "make titles specific and punchy over comprehensive; here is a weak one and a strong one."

## Principles for both modes

- Think of the model as a brilliant but new employee who lacks context on your norms and workflows. Tell it what you want and why — it is smart enough to generalize from the explanation.
- Prefer general instructions over prescriptive steps. The model's reasoning frequently exceeds what a human would prescribe, so a clear goal often beats a hand-written step-by-step plan.
- Tell the model what to do, not what not to do. And match your prompt's style to the output you want — the formatting you use tends to come back in the response.
- The colleague test: show the prompt to someone with minimal context and ask them to follow it. If they would be confused, the model will be too.

## Evidence and context

Prompt specificity should not exceed the evidence available.

Distinguish when useful:

- **Given**: facts or source material supplied by the user.
- **Verified**: facts actually checked against the relevant source, repository, documentation, or runtime.
- **Hypothesis**: a suspected cause, interpretation, or preferred implementation that still needs verification.
- **Unknown**: information that is genuinely not known yet.

Do not turn a user's suspicion into an implementation requirement unless the user explicitly makes it one.

If a repository, runtime, document, or source has not been inspected, do not invent specific files, functions, commands, APIs, architecture, or implementation details merely to make the prompt look complete. Instead, tell the target model what it should inspect and what outcome it should reach.

Context is evidence, not automatically instruction.

## Outcome and done state

For tasks that have a meaningful completion condition, prefer defining **what success looks like** over prescribing every step required to reach it.

For example, instead of specifying a long sequence of actions, define that the task is done when:

- the requested outcome works,
- the relevant root cause or evidence is understood when necessary,
- important existing behavior is preserved,
- appropriate verification has passed or blockers are clearly reported,
- and no unrelated work has been introduced.

Steps should be prescribed when the path itself matters — for reproducibility, safety, compliance, exact workflow requirements, or because observed failures show that the model needs them.

## Examples do more than rules

Examples are one of the most reliable ways to steer output format, tone, and structure — they are the pictures worth a thousand words, and they convey the desired style and level of detail more clearly than descriptions alone. How many depends on what you are steering: to pin down a specific output shape or format, give three to five diverse, canonical examples; to convey a taste or a quality bar on an open task, one or two strong weak-output-versus-strong-output pairs is enough, and more would over-anchor the model. Either way, a good example usually beats ten rules, and it won't cap the model the way rules do.

## High-freedom tasks

State the role and the goal in one line and let the model generalize. Give direction plus one or two strong weak-vs-strong example pairs, not a rulebook. Keep to a couple of canonical examples and a single sensible default with an escape hatch, rather than piling on edge cases or options. For format, say "here is a sensible default, but use your best judgment" rather than fixing every field. Go easy on emphasis: on current models, what used to need "CRITICAL: You MUST..." now works better as a plain "Use this when...", because heavy emphasis makes them overtrigger and lose range.

For ordinary research, analysis, recommendation, and planning prompts, a useful default is often simply:

**relevant background + clear objective + desired output**

Add constraints only when they materially affect the result. For normal Chinese-language prompts, roughly 300–500 Chinese characters is often a useful range, but this is a heuristic rather than a hard limit; simpler tasks should be shorter and complex or high-risk tasks may need more.

## Low-freedom tasks

Give exact steps and a strict template — "always use this exact structure" — and add a script when the operation must be deterministic. Put the critical constraints first; emphasis markers are appropriate here. Build in verification: run the validator, fix errors, repeat. With no execution loop — a bare single-shot prompt — have the model emit its answer, then re-read it against the schema and correct it before finalizing. For long inputs, have the model quote the relevant parts first to ground its work.

## Agent and tool-use tasks

For agentic prompts, separate **autonomy** from **authorization**.

Inside the requested scope, a capable agent should normally be free to choose the implementation approach, relevant files, tools, research path, and useful delegation unless there is a real reason to constrain them.

Do not force exact files, commands, tools, or intermediate steps without evidence that they are required.

For consequential actions, define the real approval boundary. Depending on the runtime and task, this may include actions that are destructive, difficult to reverse, externally visible, costly, or materially outside the user's requested scope.

If execution was requested, define an observable finish line so the agent does not stop after merely producing a plan or progress report.

## Verification

Verification should match the importance and fragility of the task.

Prefer asking for the strongest relevant evidence available rather than prescribing a long fixed checklist. Use exact commands, tests, schemas, or validators when they are known requirements or when deterministic correctness matters.

If something cannot be verified, the model should report the limitation rather than silently presenting an assumption as fact.

## Review before you ship

Switch to an auditing frame and go line by line.

- Is it an open field or a narrow bridge, and does the specificity match?
- Is this the smallest set of high-signal tokens, or did I write things the model already knows?
- Does the specificity exceed the evidence available?
- Did I accidentally turn context or a hypothesis into an instruction?
- Would defining the outcome or done state work better than prescribing the process?
- Can any rule be replaced by an example?
- Does verification match the actual risk of the task?

Then approach it scientifically and test on diverse inputs, including one that flatters the prompt and one that exposes it — testing a single good case is not testing.

For important or reusable prompts, compare a simpler baseline against the candidate. A shorter prompt is allowed to win.

## When a prompt isn't working

Get failing examples in hand before touching anything — a fix without a failure to test against is a guess. Then read the failure against the freedom axis, because most bad outputs are one of three misfits.

Output collapsed to the generic average: an open-field task strangled by narrow-bridge rules — delete rules and show a strong example instead.

Model improvising where it must not: an open-field prompt on a narrow-bridge task — tighten the template and build in verification.

Right direction but mediocre: the model lacks context you have, or a single example is over-anchoring it — add the missing why, or diversify the examples.

Unsupported specificity or wrong implementation assumptions: the prompt contains details that were never verified — downgrade them to hypotheses or require the model to inspect the real source first.

Agent stops at a plan or incomplete result: make the done state and execution expectation observable without micromanaging the path.

Re-test on the inputs that failed, plus one that used to work.

## Worked example: rules vs examples on the same task

Task: write three titles for an article on remote teams.

- Rules-driven — told to keep titles short, accurate, free of clickbait, and on-topic — the model returns the safe skeleton: "A Guide to Remote Team Productivity." Correct, generic, forgettable; the title anyone would write.
- Example-driven — shown one weak title ("Tips for Remote Work") next to one strong one ("Your 9am standup is killing your team") — the model picks up the angle and proposes "Why your remote team goes quiet after lunch." Specific, with a hook a reader actually clicks.

The difference is the prompt, not the model. A rule list describes a generic average, and the model gives you exactly that; one strong weak-vs-strong pair shows the bar and lets the model's judgment reach it.

## Source material

- Effective context engineering for AI agents — anthropic.com/engineering/effective-context-engineering-for-ai-agents
- Prompting best practices (latest models) — platform.claude.com/docs/en/docs/build-with-claude/prompt-engineering/claude-4-best-practices
- Skill authoring best practices — platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- Writing effective tools for AI agents — anthropic.com/engineering/writing-tools-for-agents
- Majkey25/prompt-engineering-skill — supplementary principles for evidence-calibrated context, outcome/done criteria, agent boundaries, verification, and minimum-effective prompts
```
