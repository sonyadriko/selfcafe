# Skills

Custom skills and workflows used in this project.

## Used Skills

| Skill | Purpose | When Used |
|-------|---------|----------|
| `superpowers:brainstorming` | Requirement gathering, design exploration | Initial project phase |
| `superpowers:writing-plans` | Create implementation plans from design | After brainstorming |
| `superpowers:subagent-driven-development` | Execute plans with fresh subagents | Implementation phase |
| `superpowers:code-review` | Review code quality and spec compliance | After task completion |
| `caveman:caveman` | Token-optimized communication mode | Active throughout |

## Skill: `brainstorming`

**Purpose**: Transform ideas into designs through dialogue

**Process**:
1. Explore project context (files, docs, commits)
2. Ask clarifying questions one at a time
3. Propose 2-3 approaches with trade-offs
4. Present design for approval
5. Write design document to `docs/plans/YYYY-MM-DD-<topic>-design.md`

**Outcome for this project**:
- Identified 3 user roles (Pelanggan, Kasir, Staff/Admin)
- Confirmed pay-at-counter flow
- Specified menu management requirements
- Chose monolithic architecture

## Skill: `writing-plans`

**Purpose**: Create detailed implementation plans from specs

**Requirements**:
- Exact file paths
- Complete code in plan (not "add validation")
- Exact commands with expected output

**Plan Structure**:
```markdown
# [Feature Name] Implementation Plan

**Goal:** [One sentence]

**Architecture:** [2-3 sentences]

**Tech Stack:** [Key technologies]

---
## PHASE 1: ...
### Task N: [Component Name]
**Files:** Create/Modify
**Step 1:** Write failing test
**Step 2:** Run test
**Step 3:** Implement
**Step 4:** Run test
**Step 5:** Commit
```

**Outcome**: 17-task plan covering setup, models, auth, customer, admin

## Skill: `subagent-driven-development`

**Purpose**: Execute plans with fresh subagent + two-stage review

**Process per Task**:
1. Dispatch implementer subagent with full task text
2. Implementer asks questions → answer
3. Implementer completes + commits
4. Spec compliance review → fix if needed
5. Code quality review → fix if needed
6. Mark task complete

**Review Findings**:
- Spec: 100% compliant across all tasks
- Code: Minor improvements suggested (validation consistency)

## Skill: `caveman`

**Purpose**: Token-optimized communication (60-90% savings)

**Intensity Levels**:
- `lite` - Short responses, some articles
- `full` - Drop articles, fragments OK (default)
- `ultra` - Maximum compression

**Pattern**: `[thing] [action] [reason]. [next step].`

**Example**:
```
Instead: "Sure! I'd be happy to help you with that. The issue..."
Caveman: "Bug in auth middleware. Fix: bcrypt.compare use <=. Commit:"
```

## Skill Workflows

### Full Project Workflow
```
brainstorming → writing-plans → subagent-driven-development → code-review → finishing-a-development-branch
```

### Per-Task Workflow
```
Dispatch implementer → Self-review → Spec review → Code review → Commit → Next task
```

## Related Documentation

- **[CLAUDE.md](CLAUDE.md)** - Project overview and architecture
- **[agents.md](agents.md)** - AI agents and session statistics
- **[design.md](design.md)** - Mastercard design system specification

## Project References

This project uses **Claude Code (Opus 4.6)** as the primary AI assistant with the `caveman` mode enabled for token optimization.

**Development Statistics** (from `agents.md`):
- 15+ commits
- 40+ files created
- ~3000+ lines of code
- Mastercard-inspired CSS (~600 lines)

## Project-Specific Patterns

### Design System Application
When applying Mastercard design system from `design.md`:
1. Use Canvas Cream `#F3F0EE` as default background
2. Primary CTAs: Ink Black `#141413`, 20px radius
3. Headlines: Inter 500, -2% letter-spacing
4. Body: Inter 450 weight
5. Cards: 40px radius, soft shadows

### Code Generation Guidelines
- Use SQLAlchemy 2.0+ syntax
- Pydantic v2: `from_attributes = True` instead of `orm_mode = True`
- FastAPI dependencies: `Depends(get_db)` pattern
- Type hints: Use modern `str | None` instead of `Optional[str]`

### Commit Message Format
```
feat: [scope] [description]

[optional details]

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```
