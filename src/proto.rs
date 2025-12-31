// Protocol buffer module
// Include all generated proto modules
pub mod vcsec;
pub mod car_server;
pub mod errors;
pub mod keys;
pub mod managed_charging;
pub mod signatures;
pub mod universal_message;

// The following modules are part of the CarServer package and are generated into car_server.rs
// pub use car_server as vehicle;
// pub use car_server as common;

// Include google protobuf types
pub mod google;
