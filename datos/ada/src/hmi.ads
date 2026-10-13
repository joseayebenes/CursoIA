with Tracks; use Tracks;

--  The operator display. This version writes each message to standard
--  output; the real one sends the TRACK, TRACK_DELETED and ALARM messages
--  defined in the ICD.
package HMI is

   procedure Show_Track (T : Track);

   procedure Remove_Track (Id : Track_Id);

   procedure Show_Alarm (Id : Track_Id; Text : String);

   procedure Acknowledge (Id : Track_Id);
   --  The operator acknowledges the alarm of a track.

   function Alarm_Active (Id : Track_Id) return Boolean;

end HMI;
