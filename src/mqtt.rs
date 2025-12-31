// MQTT client module using rumqttd

use log::{debug, info};
use rumqttd::{Client, MqttOptions, Notification, QoS};
use crate::config::MqttConfig;

pub struct MqttClient {
    client: Client,
    config: MqttConfig,
}

impl MqttClient {
    pub async fn new(config: MqttConfig) -> Result<Self, Box<dyn std::error::Error>> {
        let mut mqttoptions = MqttOptions::new("hass-tesla-ble", &config.host, config.port);
        
        if let Some(username) = &config.username {
            mqttoptions.set_credentials(username, config.password.as_deref().unwrap_or(""));
        }

        info!("Connecting to MQTT broker: {}:{}", config.host, config.port);
        let (client, mut eventloop) = Client::new(mqttoptions, 10);

        // Start event loop in background
        tokio::spawn(async move {
            loop {
                match eventloop.poll().await {
                    Ok(Notification::ConnAck(_)) => {
                        info!("MQTT Connected");
                    }
                    Ok(notification) => {
                        debug!("MQTT event: {:?}", notification);
                    }
                    Err(e) => {
                        eprintln!("MQTT event loop error: {:?}", e);
                        break;
                    }
                }
            }
        });

        Ok(MqttClient {
            client,
            config,
        })
    }

    pub fn host(&self) -> &str {
        &self.config.host
    }

    // TODO: Implement Home Assistant MQTT discovery
    pub async fn publish_discovery(
        &self,
        component: &str,
        name: &str,
        config_value: serde_json::Value,
    ) -> Result<(), Box<dyn std::error::Error>> {
        let topic = format!(
            "{}/{}/{}/config",
            self.config.discovery_prefix, component, name
        );
        let payload = serde_json::to_string(&config_value)?;

        info!("Publishing discovery config to: {}", topic);
        self.client
            .publish(topic, QoS::AtLeastOnce, false, payload)
            .await?;

        Ok(())
    }

    // TODO: Implement state publishing
    pub async fn publish_state(
        &self,
        topic: &str,
        payload: &str,
    ) -> Result<(), Box<dyn std::error::Error>> {
        info!("Publishing state to: {}", topic);
        self.client
            .publish(topic, QoS::AtLeastOnce, false, payload)
            .await?;

        Ok(())
    }

    // TODO: Implement command subscription
    pub async fn subscribe_to_commands(&self, topic: &str) -> Result<(), Box<dyn std::error::Error>> {
        info!("Subscribing to commands on: {}", topic);
        self.client.subscribe(topic, QoS::AtMostOnce).await?;
        Ok(())
    }
}
