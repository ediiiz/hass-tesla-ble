fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Create output directory for proto-generated code
    std::fs::create_dir_all("src/proto")?;

    // Compile protocol buffer definitions
    prost_build::Config::new()
        .out_dir("src/proto")
        .compile_protos(
            &[
                "proto/vcsec.proto",
                "proto/vehicle.proto",
                "proto/car_server.proto",
                "proto/common.proto",
                "proto/errors.proto",
                "proto/keys.proto",
                "proto/managed_charging.proto",
                "proto/signatures.proto",
                "proto/universal_message.proto",
                "proto/google/protobuf/timestamp.proto",
            ],
            &["proto/"],
        )?;

    // Rebuild if any proto file changes
    println!("cargo:rerun-if-changed=proto/");
    println!("cargo:rerun-if-changed=proto/vcsec.proto");
    println!("cargo:rerun-if-changed=proto/vehicle.proto");
    println!("cargo:rerun-if-changed=proto/car_server.proto");
    println!("cargo:rerun-if-changed=proto/common.proto");
    println!("cargo:rerun-if-changed=proto/errors.proto");
    println!("cargo:rerun-if-changed=proto/keys.proto");
    println!("cargo:rerun-if-changed=proto/managed_charging.proto");
    println!("cargo:rerun-if-changed=proto/signatures.proto");
    println!("cargo:rerun-if-changed=proto/universal_message.proto");

    Ok(())
}
