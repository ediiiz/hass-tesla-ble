// Tesla BLE Local Control for Home Assistant
// Work in Progress - Not yet functional

use log::info;
use tokio::signal;

mod bluetooth;
mod mqtt;
mod proto;
mod config;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // Initialize logger
    env_logger::Builder::from_default_env()
        .init();

    info!("Starting Tesla BLE Local Control for Home Assistant");

    // Load configuration
    let config = config::load_config()
        .expect("Failed to load configuration");

    info!("Configuration loaded successfully");
    info!("Vehicle VIN: {}", config.vehicle.vin);

    // Initialize MQTT client
    let mqtt_client = mqtt::MqttClient::new(config.mqtt)
        .await
        .expect("Failed to initialize MQTT client");

    info!("MQTT client connected to {}", mqtt_client.host());

    // Initialize BLE adapter
    let ble_adapter = bluetooth::BleAdapter::new(config.bluetooth.adapter)
        .await
        .expect("Failed to initialize BLE adapter");

    info!("BLE adapter initialized: {}", ble_adapter.name());

    // TODO: Implement vehicle discovery
    // TODO: Implement vehicle pairing flow
    // TODO: Implement MQTT entity publishing
    // TODO: Implement vehicle state monitoring
    // TODO: Implement command execution

    info!("Setup complete. Waiting for vehicle...");

    // Wait for shutdown signal
    signal::ctrl_c().await?;
    info!("Shutting down...");

    Ok(())
}
