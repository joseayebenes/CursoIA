--  Track data shared by every package of the Track Management Software.
package Tracks is

   Max_Tracks : constant := 1_000;

   type Track_Id is range 1 .. Max_Tracks;

   type Seconds is new Duration;
   --  Time since the software started.

   type Position is record
      X, Y : Float := 0.0;   --  metres from the sensor
   end record;

   type Track is record
      Id          : Track_Id := Track_Id'First;
      Target      : Natural  := 0;     --  target number given by the sensor
      Pos         : Position;
      Last_Report : Seconds  := 0.0;
      In_Use      : Boolean  := False;
   end record;

   Stale_Timeout : constant Seconds := 10.0;
   --  A track with no report for this long is stale and must be deleted.

   Purge_Period : constant Seconds := 1.0;
   --  Stale tracks are purged once per period.

end Tracks;
