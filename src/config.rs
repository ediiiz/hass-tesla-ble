// Configuration module for Tesla BLE addon

use serde::{Deserialize, Serialize};
use std::fs;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub mqtt: MqttConfig,
    pub bluetooth: BluetoothConfig,
    pub vehicle: VehicleConfig,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MqttConfig {
    pub host: String,
    #[serde(default = "default_port")]
    pub port: u16,
    #[serde(default)]
    pub username: Option<String>,
    #[serde(default)]
    pub password: Option<String>,
    #[serde(default = "default_discovery_prefix")]
    pub discovery_prefix: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BluetoothConfig {
    pub adapter: String,
    pub mode: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VehicleConfig {
    pub vin: String,
}

fn default_port() -> u16 {
    1883
}

fn default_discovery_prefix() -> String {
    "homeassistant".to_string()
}

pub fn load_config() -> Result<Config, Box<dyn std::error::Error>> {
    let config_path = "/config/options.json";
    let config_content = fs::read_to_string(config_path)?;
    let config: Config = serde_json::from_str(&config_content)?;
    Ok(config)
}
