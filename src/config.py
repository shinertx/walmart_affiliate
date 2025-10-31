import json
from pathlib import Path
from typing import Dict, Any, List

class Config:
    """Configuration management for Walmart API testing"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = Path(config_file)
        self.default_config = {
            "testing": {
                "default_batch_sizes": [1, 5, 10, 25, 50, 100, 200, 400, 500, 1000],
                "max_limit_test_sizes": [1000, 2000, 5000, 10000, 20000],
                "iterations_per_size": 1,
                "delay_between_requests": 2.0,
                "test_categories": {
                    "electronics": "3944",
                    "home_garden": "1072864",
                    "clothing": "5438",
                    "sports": "4125"
                }
            },
            "api": {
                "request_timeout": 30,
                "max_retries": 3,
                "rate_limit_delay": 1.0
            },
            "output": {
                "save_json": True,
                "save_csv": True,
                "create_charts": True,
                "results_directory": "results"
            }
        }
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file, create default if doesn't exist"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        else:
            self._save_config(self.default_config)
            return self.default_config.copy()
    
    def _save_config(self, config: Dict[str, Any]):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def get(self, key_path: str, default=None):
        """Get configuration value using dot notation (e.g., 'testing.batch_sizes')"""
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def update(self, key_path: str, value: Any):
        """Update configuration value and save to file"""
        keys = key_path.split('.')
        config_ref = self.config
        
        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in config_ref:
                config_ref[key] = {}
            config_ref = config_ref[key]
        
        # Set the value
        config_ref[keys[-1]] = value
        self._save_config(self.config)
    
    def get_batch_sizes(self) -> List[int]:
        """Get configured batch sizes for testing"""
        return self.get('testing.default_batch_sizes', [1, 10, 25, 50, 100])
    
    def get_test_categories(self) -> Dict[str, str]:
        """Get available test categories"""
        return self.get('testing.test_categories', {})
    
    def reset_to_defaults(self):
        """Reset configuration to defaults"""
        self.config = self.default_config.copy()
        self._save_config(self.config)