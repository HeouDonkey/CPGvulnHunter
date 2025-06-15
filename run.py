

from CPGvulnHunter.core.engine import VulnerabilityEngine


if __name__ == "__main__":
    # 示例：快速分析
    
    src_path = "/home/nstl/data/CPGvulnHunter/test/test_case/juliet/C/testcases/CWE78_OS_Command_Injection/s01/CWE78_OS_Command_Injection__char_connect_socket_execl_01.c"
    config_file = "/home/nstl/data/CPGvulnHunter/config.yml"
    engine = VulnerabilityEngine(config_file=config_file)
    engine.run(src_path=src_path, passes=['cwe78'])