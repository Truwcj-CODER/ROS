#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};



// Corresponds to drive_base_msgs__msg__CommandHeader
/// Standard header for commands

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct CommandHeader {
    /// source timestamp
    pub stamp: builtin_interfaces::msg::Time,

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
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::CommandHeader::default())
  }
}

impl rosidl_runtime_rs::Message for CommandHeader {
  type RmwMsg = super::msg::rmw::CommandHeader;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        stamp: builtin_interfaces::msg::Time::into_rmw_message(std::borrow::Cow::Owned(msg.stamp)).into_owned(),
        command_id: msg.command_id,
        expected_period: msg.expected_period,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        stamp: builtin_interfaces::msg::Time::into_rmw_message(std::borrow::Cow::Borrowed(&msg.stamp)).into_owned(),
      command_id: msg.command_id,
      expected_period: msg.expected_period,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      stamp: builtin_interfaces::msg::Time::from_rmw_message(msg.stamp),
      command_id: msg.command_id,
      expected_period: msg.expected_period,
    }
  }
}


// Corresponds to drive_base_msgs__msg__BaseInfo

// This struct is not documented.
#[allow(missing_docs)]

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct BaseInfo {
    /// identifying information
    /// a, hopefully unique, id
    pub hw_id: u32,

    /// timestamp as returned by the hardware
    pub hw_timestamp: u32,

    /// wall clock timestamp
    pub stamp: builtin_interfaces::msg::Time,

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
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::BaseInfo::default())
  }
}

impl rosidl_runtime_rs::Message for BaseInfo {
  type RmwMsg = super::msg::rmw::BaseInfo;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        hw_id: msg.hw_id,
        hw_timestamp: msg.hw_timestamp,
        stamp: builtin_interfaces::msg::Time::into_rmw_message(std::borrow::Cow::Owned(msg.stamp)).into_owned(),
        x: msg.x,
        y: msg.y,
        orientation: msg.orientation,
        forward_velocity: msg.forward_velocity,
        rotational_velocity: msg.rotational_velocity,
        battery_voltage_pct: msg.battery_voltage_pct,
        power_supply: msg.power_supply,
        overcurrent: msg.overcurrent,
        blocked: msg.blocked,
        in_collision: msg.in_collision,
        at_cliff: msg.at_cliff,
        safety_state: msg.safety_state,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      hw_id: msg.hw_id,
      hw_timestamp: msg.hw_timestamp,
        stamp: builtin_interfaces::msg::Time::into_rmw_message(std::borrow::Cow::Borrowed(&msg.stamp)).into_owned(),
      x: msg.x,
      y: msg.y,
      orientation: msg.orientation,
      forward_velocity: msg.forward_velocity,
      rotational_velocity: msg.rotational_velocity,
      battery_voltage_pct: msg.battery_voltage_pct,
      power_supply: msg.power_supply,
      overcurrent: msg.overcurrent,
      blocked: msg.blocked,
      in_collision: msg.in_collision,
      at_cliff: msg.at_cliff,
      safety_state: msg.safety_state,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      hw_id: msg.hw_id,
      hw_timestamp: msg.hw_timestamp,
      stamp: builtin_interfaces::msg::Time::from_rmw_message(msg.stamp),
      x: msg.x,
      y: msg.y,
      orientation: msg.orientation,
      forward_velocity: msg.forward_velocity,
      rotational_velocity: msg.rotational_velocity,
      battery_voltage_pct: msg.battery_voltage_pct,
      power_supply: msg.power_supply,
      overcurrent: msg.overcurrent,
      blocked: msg.blocked,
      in_collision: msg.in_collision,
      at_cliff: msg.at_cliff,
      safety_state: msg.safety_state,
    }
  }
}


// Corresponds to drive_base_msgs__msg__CommandStatus
/// command has been accepted

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct CommandStatus {
    /// timestamp of this message
    pub stamp: builtin_interfaces::msg::Time,

    /// command this pertains to
    pub cmd_header: super::msg::CommandHeader,

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
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::CommandStatus::default())
  }
}

impl rosidl_runtime_rs::Message for CommandStatus {
  type RmwMsg = super::msg::rmw::CommandStatus;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        stamp: builtin_interfaces::msg::Time::into_rmw_message(std::borrow::Cow::Owned(msg.stamp)).into_owned(),
        cmd_header: super::msg::CommandHeader::into_rmw_message(std::borrow::Cow::Owned(msg.cmd_header)).into_owned(),
        status: msg.status,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        stamp: builtin_interfaces::msg::Time::into_rmw_message(std::borrow::Cow::Borrowed(&msg.stamp)).into_owned(),
        cmd_header: super::msg::CommandHeader::into_rmw_message(std::borrow::Cow::Borrowed(&msg.cmd_header)).into_owned(),
      status: msg.status,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      stamp: builtin_interfaces::msg::Time::from_rmw_message(msg.stamp),
      cmd_header: super::msg::CommandHeader::from_rmw_message(msg.cmd_header),
      status: msg.status,
    }
  }
}


// Corresponds to drive_base_msgs__msg__TRVCommand
/// Command a mobile base by Translational and Rotational Velocity
/// Primarily intended for differential drive bases.

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct TRVCommand {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: super::msg::CommandHeader,


    // This member is not documented.
    #[allow(missing_docs)]
    pub translational_velocity: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub rotational_velocity: f32,

}



impl Default for TRVCommand {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::TRVCommand::default())
  }
}

impl rosidl_runtime_rs::Message for TRVCommand {
  type RmwMsg = super::msg::rmw::TRVCommand;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: super::msg::CommandHeader::into_rmw_message(std::borrow::Cow::Owned(msg.header)).into_owned(),
        translational_velocity: msg.translational_velocity,
        rotational_velocity: msg.rotational_velocity,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: super::msg::CommandHeader::into_rmw_message(std::borrow::Cow::Borrowed(&msg.header)).into_owned(),
      translational_velocity: msg.translational_velocity,
      rotational_velocity: msg.rotational_velocity,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      header: super::msg::CommandHeader::from_rmw_message(msg.header),
      translational_velocity: msg.translational_velocity,
      rotational_velocity: msg.rotational_velocity,
    }
  }
}


