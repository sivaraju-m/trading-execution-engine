#!/usr/bin/env python3
"""
Trading Execution Engine Deployment Validation Script

This script validates that the trading execution engine is properly configured
and all dependencies are correctly installed.
"""

import sys
import os
import logging
from pathlib import Path
from typing import List, Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom exception for validation failures"""
    pass

class TradingExecutionEngineValidator:
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_results = {}
        
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all validation tests"""
        logger.info("🚀 Starting Trading Execution Engine deployment validation...")
        
        test_suites = [
            ("Import Tests", self._test_imports),
            ("Configuration Files", self._test_config_files),
            ("Entry Points", self._test_entry_points),
            ("Package Installation", self._test_package_installation),
            ("Docker Environment", self._test_docker_environment),
            ("Basic Functionality", self._test_basic_functionality),
        ]
        
        for suite_name, test_func in test_suites:
            logger.info(f"\n{'='*50}")
            logger.info(f"Running: {suite_name}")
            logger.info(f"{'='*50}")
            
            try:
                test_func()
                self.test_results[suite_name] = True
                self.tests_passed += 1
                logger.info(f"✅ {suite_name} PASSED")
            except Exception as e:
                self.test_results[suite_name] = False
                self.tests_failed += 1
                logger.error(f"❌ {suite_name} FAILED: {str(e)}")
        
        return self.test_results
    
    def _test_imports(self):
        """Test critical imports"""
        logger.info("🔍 Testing critical imports...")
        
        critical_imports = [
            ('pandas', 'pandas'),
            ('numpy', 'numpy'),
            ('kiteconnect', 'kiteconnect'),
            ('trading_data_pipeline', 'trading_data_pipeline'),
            ('strategy_engine', 'strategy_engine'),
            ('shared_services', 'shared_services'),
            ('yfinance', 'yfinance'),
            ('scikit-learn', 'sklearn'),
            ('ta-lib', 'talib'),
            ('yaml', 'yaml'),
            ('websockets', 'websockets'),
            ('trading_execution_engine', 'trading_execution_engine'),
        ]
        
        for display_name, import_name in critical_imports:
            try:
                __import__(import_name)
                logger.info(f"✅ {display_name}")
            except ImportError as e:
                raise ValidationError(f"Failed to import {display_name}: {e}")
    
    def _test_config_files(self):
        """Test configuration files exist"""
        logger.info("🔍 Testing configuration files...")
        
        required_files = [
            'requirements.txt',
            'setup.py',
            'Dockerfile',
        ]
        
        for file_path in required_files:
            if os.path.exists(file_path):
                logger.info(f"✅ {file_path}")
            else:
                raise ValidationError(f"Missing required file: {file_path}")
    
    def _test_entry_points(self):
        """Test entry point scripts exist and are executable"""
        logger.info("🔍 Testing entry point scripts...")
        
        entry_points = [
            'bin/automated_trading_system.py',
            'bin/live_trading_flow.py',
        ]
        
        for entry_point in entry_points:
            if os.path.exists(entry_point):
                logger.info(f"✅ {entry_point}")
            else:
                raise ValidationError(f"Missing entry point: {entry_point}")
    
    def _test_package_installation(self):
        """Test package installation"""
        logger.info("🔍 Testing package installation...")
        
        try:
            import trading_execution_engine
            # Try to access main components
            logger.info("✅ Package installation successful")
        except Exception as e:
            raise ValidationError(f"Package installation failed: {e}")
    
    def _test_docker_environment(self):
        """Test Docker environment if running in container"""
        logger.info("🔍 Testing Docker environment...")
        
        # Check if running in Docker
        if os.path.exists('/.dockerenv'):
            logger.info("✅ Running in Docker container")
            
            # Test file permissions
            try:
                test_file = '/tmp/test_write_permissions.txt'
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                logger.info("✅ File write permissions")
            except Exception as e:
                raise ValidationError(f"Docker file permissions issue: {e}")
            
            # Test working directory
            if os.getcwd() == '/app':
                logger.info("✅ Correct working directory")
            else:
                raise ValidationError(f"Wrong working directory: {os.getcwd()}")
        else:
            logger.info("✅ Running in local environment")
    
    def _test_basic_functionality(self):
        """Test basic functionality"""
        logger.info("🔍 Testing basic functionality...")
        
        # Test pandas
        try:
            import pandas as pd
            df = pd.DataFrame({'test': [1, 2, 3]})
            assert len(df) == 3
            logger.info("✅ Pandas functionality")
        except Exception as e:
            raise ValidationError(f"Pandas functionality test failed: {e}")
        
        # Test numpy
        try:
            import numpy as np
            arr = np.array([1, 2, 3])
            assert len(arr) == 3
            logger.info("✅ NumPy functionality")
        except Exception as e:
            raise ValidationError(f"NumPy functionality test failed: {e}")
        
        # Test YAML
        try:
            import yaml
            test_data = {'test': 'value'}
            yaml_str = yaml.dump(test_data)
            parsed = yaml.safe_load(yaml_str)
            assert parsed['test'] == 'value'
            logger.info("✅ YAML functionality")
        except Exception as e:
            raise ValidationError(f"YAML functionality test failed: {e}")
    
    def print_summary(self):
        """Print validation summary"""
        logger.info(f"\n{'='*60}")
        logger.info("VALIDATION SUMMARY")
        logger.info(f"{'='*60}")
        
        for test_name, passed in self.test_results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            logger.info(f"{test_name}: {status}")
        
        if self.tests_failed == 0:
            logger.info(f"\n🎉 ALL TESTS PASSED! Trading Execution Engine is ready for deployment.")
            return True
        else:
            logger.error(f"\n💥 {self.tests_failed} TEST(S) FAILED! Please fix the issues before deployment.")
            return False

def main():
    """Main function"""
    validator = TradingExecutionEngineValidator()
    
    try:
        validator.run_all_tests()
        success = validator.print_summary()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n⏹️  Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n💥 Unexpected error during validation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
