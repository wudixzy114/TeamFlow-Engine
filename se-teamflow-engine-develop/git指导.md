### **请先注册登录清华** git

清华 git 地址： https://git.tsinghua.edu.cn/
请大家将清华 git 账号的名称或者邮箱发送到群里，我把大家拉到小组中

### **AI 助手大作业项目协作指南 (GitLab 版)**

大家好，

欢迎加入我们的 AI 助手项目！为了确保我们能够高效、有序地协作，避免代码冲突和混乱，请每一位成员严格遵守以下 Git 和 GitLab 工作流程。这份文档将是我们在整个项目开发过程中的行为准则。

#### **一、核心原则**

1.  **绝不直接向 `main` 或 `develop` 分支推送代码 (NEVER push to `main`/`develop` directly)。**
2.  **所有新功能和 Bug 修复都必须在独立的特性分支 (Feature Branch) 上进行。**
3.  **代码合并必须通过 GitLab 的合并请求 (Merge Request) 进行，并经过至少一名其他成员的审查 (Code Review)。**
4.  **在开始新任务前，务必从 `develop` 分支拉取最新代码，保持本地环境同步。**
5.  **保持提交信息 (Commit Message) 的清晰和规范。**

---

#### **二、基本设置 (只需做一次)**

1.  **克隆团队仓库**:
    打开你的终端，使用 `git clone` 命令将我们的团队项目克隆到你的本地电脑。请确保你使用的是我们小组 Group 下的仓库链接，而不是助教的原始仓库。

    ```bash
    # 在 GitLab 项目页面点击蓝色的 "Clone" 按钮获取链接
    git clone [我们团队项目的HTTPS或SSH链接]
    cd [项目文件夹名称]
    ```

2.  **设置你的 Git 用户名和邮箱**:
    这非常重要，它能让大家知道每一次提交是谁完成的。

    ```bash
    git config --global user.name "你的名字拼音"
    git config --global user.email "你的清华邮箱"
    ```

3.  **创建 `develop` 分支 (仅组长操作一次)**:
    我们的 `main` 分支将用于存放稳定、可演示的版本。日常开发将在 `develop` 分支上进行聚合。
    ```bash
    # 第一次设置时，组长需要创建并推送develop分支
    git checkout -b develop
    git push -u origin develop
    ```
    之后，组长需要在 GitLab 上将 `develop` 分支设置为**受保护分支 (Protected Branch)**，防止成员误操作直接推送。

---

#### **三、标准开发流程 (每次开发新功能时重复)**

假设你被分配了开发“网络搜索 (`/search`)”功能的任务。

**第一步：同步本地 `develop` 分支**

在开始任何新工作之前，确保你的本地 `develop` 分支是最新的。

```bash
# 1. 切换到 develop 分支
git checkout develop

# 2. 从远程仓库拉取最新的更改
git pull origin develop
```

**第二步：创建你的特性分支**

从最新的 `develop` 分支上创建一个属于你自己的、描述性强的分支。分支命名规范：`feature/你的名字-功能简述`。

```bash
# 例如: feature/zhangsan-search-module
git checkout -b feature/zhangsan-search-module
```

现在，你就可以在这个 `feature/zhangsan-search-module` 分支上安心地编写你的代码了。你所有的修改和提交都只会影响这个分支，不会干扰到任何人。

**第三步：编码与提交 (Commit)**

在你的特性分支上进行开发。当你完成了一个小的、有意义的改动（比如写完了 `search.py` 的核心函数），就进行一次 `git commit`。

```bash
# 1. 查看你修改了哪些文件
git status

# 2. 将你想要提交的文件添加到暂存区 (例如 search.py 和 app.py)
git add search.py app.py

# 3. 提交你的更改，并写下清晰的提交信息
git commit -m "feat: 实现网络搜索核心函数 search()"
```

> **提交信息规范 (Commit Message Convention)**:
> 请使用 `类型: 描述` 的格式。
>
> - `feat`: 新功能 (feature)
> - `fix`: 修复 bug
> - `docs`: 文档变更
> - `style`: 代码格式调整 (不影响代码运行的变动)
> - `refactor`: 重构 (既不是增加功能，也不是修复 bug)
>
> 示例: `feat: 完成网页总结模块的p标签提取`

**第四步：推送你的特性分支到 GitLab**

当你觉得功能开发完成，或者希望让大家看到你的进展时，将你的特性分支推送到远程仓库。

```bash
# -u 参数会建立本地分支和远程分支的链接，以后只需 git push 即可
git push `-u` origin feature/zhangsan-search-module
```

**第五步：创建合并请求 (Merge Request)**

1.  推送成功后，GitLab 会在终端输出一个链接，或者你直接访问我们的 GitLab 项目主页，会看到一个黄色提示条，引导你 "Create a merge request"。
2.  点击这个按钮，进入创建合并请求的页面。
3.  **Source branch**: 应该是你的特性分支 (`feature/zhangsan-search-module`)。
4.  **Target branch**: **必须是 `develop` 分支**。
5.  **Title**: 写一个清晰的标题，如 "完成网络搜索功能"。
6.  **Description**: 简单描述你在这个 MR 中做了什么，遇到了什么问题，或者需要审查者注意什么。
7.  **Assignee**: 指派给你自己。
8.  **Reviewer**: **指派给组长或其他至少一位组员**。这是强制性的 Code Review 环节。
9.  点击 "Create merge request"。

**第六步：代码审查与合并 (Code Review & Merge)**

1.  **审查者**: 会收到通知。他们会查看你提交的代码，在 GitLab 的界面上提出修改建议或评论。
2.  **你**: 根据审查意见，在你的本地特性分支上进行修改、提交、然后再次 `git push`。新的提交会自动更新到这个合并请求中。
3.  **循环往复**，直到审查者认为代码没有问题，并 "Approve" 了你的合并请求。
4.  **组长/审查者**: 点击 "Merge" 按钮，将你的代码安全地合并到 `develop` 分支中。合并后，可以选择删除源特性分支。

**第七步：任务完成**

你的功能已经成功地集成到了项目的主开发线中！现在你可以回到 **第一步**，开始你的下一个任务。

---

#### **四、解决冲突 (Conflict Resolution)**

如果你的合并请求与 `develop` 分支有冲突，GitLab 会提示你。这时你需要：

1.  在本地更新 `develop` 分支: `git checkout develop` -> `git pull`。
2.  切换回你的特性分支: `git checkout feature/your-branch`。
3.  将最新的 `develop` 分支合并到你的特性分支: `git merge develop`。
4.  Git 会提示哪些文件有冲突。打开这些文件，手动解决 `<<<<<<<`, `=======`, `>>>>>>>` 标记的部分。
5.  解决后，保存文件，然后执行 `git add [冲突文件]` -> `git commit`。
6.  最后 `git push` 你修复冲突后的特性分支。GitLab 上的合并请求会自动更新。

---

如有任何疑问，请随时在小组群里提出。让我们一起打造一个出色的 AI 助手！
