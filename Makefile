.PHONY: help test test-unit test-integration test-all coverage lint format clean install install-dev

# 默认目标
help:
	@echo "py2joern 测试和开发命令:"
	@echo ""
	@echo "测试命令:"
	@echo "  test           - 运行所有测试"
	@echo "  test-unit      - 只运行单元测试"
	@echo "  test-integration - 只运行集成测试"
	@echo "  test-slow      - 运行标记为慢速的测试"
	@echo "  coverage       - 运行测试并生成覆盖率报告"
	@echo ""
	@echo "代码质量:"
	@echo "  lint          - 运行代码检查"
	@echo "  format        - 格式化代码"
	@echo "  type-check    - 类型检查"
	@echo ""
	@echo "环境管理:"
	@echo "  install       - 安装项目"
	@echo "  install-dev   - 安装开发依赖"
	@echo "  clean         - 清理构建文件"
	@echo ""
	@echo "文档:"
	@echo "  docs          - 生成文档"

# 测试命令
test:
	python -m pytest tests/ -v

test-unit:
	python -m pytest tests/unit/ -v

test-integration:
	python -m pytest tests/integration/ -v

test-slow:
	python -m pytest tests/ -v -m "slow"

test-quick:
	python -m pytest tests/ -v -m "not slow"

test-requires-joern:
	python -m pytest tests/ -v -m "requires_joern"

# 使用自定义测试运行器
test-runner:
	python tests/run_tests.py

test-runner-unit:
	python tests/run_tests.py --unit

test-runner-integration:
	python tests/run_tests.py --integration

# 覆盖率测试
coverage:
	python -m pytest tests/ --cov=src/py2joern --cov-report=html --cov-report=term-missing

coverage-unit:
	python -m pytest tests/unit/ --cov=src/py2joern --cov-report=html --cov-report=term-missing

coverage-xml:
	python -m pytest tests/ --cov=src/py2joern --cov-report=xml

# 代码质量
lint:
	flake8 src tests
	black --check src tests
	isort --check-only src tests

format:
	black src tests
	isort src tests

type-check:
	mypy src

# 环境管理
install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"
	pip install pytest pytest-cov pytest-mock pexpect flake8 black isort mypy

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf .tox/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# 文档
docs:
	@echo "生成文档 (需要实现)"

# 包构建
build:
	python setup.py sdist bdist_wheel

# 发布 (需要配置)
publish-test:
	twine upload --repository-url https://test.pypi.org/legacy/ dist/*

publish:
	twine upload dist/*

# 开发环境设置
dev-setup: install-dev
	pre-commit install

# 运行所有质量检查
quality: lint type-check test

# CI/CD相关
ci-test:
	python -m pytest tests/ --cov=src/py2joern --cov-report=xml --junitxml=test-results.xml

# 性能测试
performance:
	python -m pytest tests/ -v -m "slow" --durations=10

# 详细测试输出
test-verbose:
	python -m pytest tests/ -vvv --tb=long

# 并行测试 (需要pytest-xdist)
test-parallel:
	python -m pytest tests/ -n auto

# 监控文件变化自动测试 (需要pytest-watch)
test-watch:
	ptw tests/ src/
