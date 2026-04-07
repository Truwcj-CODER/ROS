#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};


#[link(name = "drive_base_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__drive_base_msgs__msg__CommandHeader() -> *const std::ffi::c_void;
}

#[link(name = "drive_base_msgs__rosidl_generator_c")]
extern "C" {
    fn drive_base_msgs__msg__CommandHeader__init(msg: *mut CommandHeader) -> bool;
    fn drive_base_msgs__msg__CommandHeader__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<CommandHeader>, size: usize) -> bool;
    fn drive_base_msgs__msg__CommandHeader__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<CommandHeader>);
    fn drive_base_msgs__msg__CommandHeader__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<CommandHeader>, out_seq: *mut rosidl_runtime_rs::Sequence<CommandHeader>) -> bool;
}

// Corresponds to drive_base_msgs__msg__CommandHeader
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]

/// Standard header for commands

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct CommandHeader {
    /// source timestamp
    pub stamp: builtin_interfaces::msg::rmw::Time,

    /// an identifier for status replies
    pub command_id: u32,

    /// by informing the base about the period we expect
    /// to send, it can implement a safety shut-off when
    /// messages take much longer.
    /// if zero, bases may estimate the period from the incoming data
    /// data stream
    pub expected_period: u16,

}



impl Default for CommandHeader {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !drive_base_msgs__msg__CommandHeader__init(&mut msg as *mut _) {
        panic!("Call to drive_base_msgs__msg__CommandHeader__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for CommandHeader {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { drive_base_msgs__msg__CommandHeader__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { drive_base_msgs__msg__CommandHeader__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { drive_base_msgs__msg__CommandHeader__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for CommandHeader {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for CommandHeader where Self: Sized {
  const TYPE_NAME: &'static str = "drive_base_msgs/msg/CommandHeader";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__drive_base_msgs__msg__CommandHeader() }
  }
}


#[link(name = "drive_base_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__drive_base_msgs__msg__BaseInfo() -> *const std::ffi::c_void;
}

#[link(name = "drive_base_msgs__rosidl_generator_c")]
extern "C" {
    fn drive_base_msgs__msg__BaseInfo__init(msg: *mut BaseInfo) -> bool;
    fn drive_base_msgs__msg__BaseInfo__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<BaseInfo>, size: usize) -> bool;
    fn drive_base_msgs__msg__BaseInfo__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<BaseInfo>);
    fn drive_base_msgs__msg__BaseInfo__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<BaseInfo>, out_seq: *mut rosidl_runtime_rs::Sequence<BaseInfo>) -> bool;
}

// Corresponds to drive_base_msgs__msg__BaseInfo
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct BaseInfo {
    /// identifying information
    /// a, hopefully unique, id
    pub hw_id: u32,

    /// timestamp as returned by the hardware
    pub hw_timestamp: u32,

    /// wall clock timestamp
    pub stamp: builtin_interfaces::msg::rmw::Time,

    /// position information (estimated, relative to starting pose)
    pub x: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub y: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub orientation: f32,

    /// should we add z?
    /// velocity information
    pub forward_velocity: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub rotational_velocity: f32,

    /// battery state
    /// range: 0-100. current battery voltage as percent of nominal.
    pub battery_voltage_pct: u8,

    /// one of the constants above
    pub power_supply: u8,

    /// diagnostic information
    /// motor overcurrent detected
    pub overcurrent: bool,

    /// True if forward direction is blocked by an obstacle
    pub blocked: bool,

    /// True if the robot is in collision (usually detected via bumper)
    pub in_collision: bool,

    /// True if the robot has detected a cliff in the forward direction
    pub at_cliff: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub safety_state: u16,

}

impl BaseInfo {

    // This constant is not documented.
    #[allow(missing_docs)]
    pub const POWER_SUPPLY_STATUS_UNKNOWN: u8 = 0;


    // This constant is not documented.
    #[allow(missing_docs)]
    pub const POWER_SUPPLY_STATUS_CHARGING: u8 = 1;


    // This constant is not documented.
    #[allow(missing_docs)]
    pub const POWER_SUPPLY_STATUS_DISCHARGING: u8 = 2;


    // This constant is not documented.
    #[allow(missing_docs)]
    pub const POWER_SUPPLY_STATUS_NOT_CHARGING: u8 = 3;


    // This constant is not documented.
    #[allow(missing_docs)]
    pub const POWER_SUPPLY_STATUS_FULL: u8 = 4;

    /// OR'able bits to communicate current safety state as determined by base sensors
    pub const SAFETY_STATE_OPERATIONAL: u16 = 1;


    // This constant is not documented.
    #[allow(missing_docs)]
    pub const SAFETY_STATE_LOW_SPEED: u16 = 2;


    // This constant is not documented.
    #[allow(missing_docs)]
    pub const SAFETY_STATE_NO_FORWARD: u16 = 4;


    // This constant is not documented.
    #[allow(missing_docs)]
    pub const SAFETY_STATE_NO_BACKWARD: u16 = 8;


    // This constant is not documented.
    #[allow(missing_docs)]
    pub const SAFETY_STATE_NO_ROTATE: u16 = 16;

}


impl Default for BaseInfo {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !drive_base_msgs__msg__BaseInfo__init(&mut msg as *mut _) {
        panic!("Call to drive_base_msgs__msg__BaseInfo__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for BaseInfo {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { drive_base_msgs__msg__BaseInfo__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { drive_base_msgs__msg__BaseInfo__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { drive_base_msgs__msg__BaseInfo__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for BaseInfo {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for BaseInfo where Self: Sized {
  const TYPE_NAME: &'static str = "drive_base_msgs/msg/BaseInfo";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__drive_base_msgs__msg__BaseInfo() }
  }
}


#[link(name = "drive_base_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__drive_base_msgs__msg__CommandStatus() -> *const std::ffi::c_void;
}

#[link(name = "drive_base_msgs__rosidl_generator_c")]
extern "C" {
    fn drive_base_msgs__msg__CommandStatus__init(msg: *mut CommandStatus) -> bool;
    fn drive_base_msgs__msg__CommandStatus__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<CommandStatus>, size: usize) -> bool;
    fn drive_base_msgs__msg__CommandStatus__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<CommandStatus>);
    fn drive_base_msgs__msg__CommandStatus__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<CommandStatus>, out_seq: *mut rosidl_runtime_rs::Sequence<CommandStatus>) -> bool;
}

// Corresponds to drive_base_msgs__msg__CommandStatus
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]

/// command has been accepted

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct CommandStatus {
    /// timestamp of this message
    pub stamp: builtin_interfaces::msg::rmw::Time,

    /// command this pertains to
    pub cmd_header: super::super::msg::rmw::CommandHeader,

    /// result of the command
    pub status: u8,

}

impl CommandStatus {

    // This constant is not documented.
    #[allow(missing_docs)]
    pub const OK: u8 = 0;

    /// the command contained requests that exceed the capabilities of the system
    /// e.g., the command speed was too high
    /// NOTE: The system will still attempt to perform as best it can
    pub const CAPABILITIES_EXCEEDED: u8 = 1;

    /// the command contained invalid values, and the system will not attempt
    /// to perform it
    pub const INVALID: u8 = 2;

    /// the command cannot be executed because the system has insufficient power to operate
    pub const POWER_INSUFFICIENT: u8 = 3;

    /// the system is currently inoperational for an unspecified reason
    /// it expects to be able to recover
    pub const TEMPORARY_FAILURE: u8 = 4;

    /// the system is inoperational indefinitely
    pub const SYSTEM_FAILURE: u8 = 5;

}


impl Default for CommandStatus {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !drive_base_msgs__msg__CommandStatus__init(&mut msg as *mut _) {
        panic!("Call to drive_base_msgs__msg__CommandStatus__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for CommandStatus {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { drive_base_msgs__msg__CommandStatus__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { drive_base_msgs__msg__CommandStatus__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { drive_base_msgs__msg__CommandStatus__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for CommandStatus {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for CommandStatus where Self: Sized {
  const TYPE_NAME: &'static str = "drive_base_msgs/msg/CommandStatus";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__drive_base_msgs__msg__CommandStatus() }
  }
}


#[link(name = "drive_base_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__drive_base_msgs__msg__TRVCommand() -> *const std::ffi::c_void;
}

#[link(name = "drive_base_msgs__rosidl_generator_c")]
extern "C" {
    fn drive_base_msgs__msg__TRVCommand__init(msg: *mut TRVCommand) -> bool;
    fn drive_base_msgs__msg__TRVCommand__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<TRVCommand>, size: usize) -> bool;
    fn drive_base_msgs__msg__TRVCommand__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<TRVCommand>);
    fn drive_base_msgs__msg__TRVCommand__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<TRVCommand>, out_seq: *mut rosidl_runtime_rs::Sequence<TRVCommand>) -> bool;
}

// Corresponds to drive_base_msgs__msg__TRVCommand
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]

/// Command a mobile base by Translational and Rotational Velocity
/// Primarily intended for differential drive bases.

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct TRVCommand {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: super::super::msg::rmw::CommandHeader,


    // This member is not documented.
    #[allow(missing_docs)]
    pub translational_velocity: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub rotational_velocity: f32,

}



impl Default for TRVCommand {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !drive_base_msgs__msg__TRVCommand__init(&mut msg as *mut _) {
        panic!("Call to drive_base_msgs__msg__TRVCommand__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for TRVCommand {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { drive_base_msgs__msg__TRVCommand__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { drive_base_msgs__msg__TRVCommand__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { drive_base_msgs__msg__TRVCommand__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for TRVCommand {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for TRVCommand where Self: Sized {
  const TYPE_NAME: &'static str = "drive_base_msgs/msg/TRVCommand";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__drive_base_msgs__msg__TRVCommand() }
  }
}


