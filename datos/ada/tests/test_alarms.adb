with Ada.Text_IO; use Ada.Text_IO;
with Tracks;      use Tracks;
with Alarms;
with HMI;

--  Unit tests of Alarms.
procedure Test_Alarms is

   Failures : Natural := 0;

   Outside : constant Position := (X => 0.0, Y => 0.0);
   Inside  : constant Position := (X => 1_500.0, Y => 0.0);

   procedure Check (Condition : Boolean; Name : String) is
   begin
      if Condition then
         Put_Line ("PASS " & Name);
      else
         Put_Line ("FAIL " & Name);
         Failures := Failures + 1;
      end if;
   end Check;

   function Track_At (Id : Track_Id; Pos : Position) return Track is
     ((Id => Id, Target => 7, Pos => Pos, Last_Report => 0.0, In_Use => True));

   --  Verifies: SRS-0007
   procedure Test_Alarm_On_Entry is
   begin
      Alarms.Check (Track_At (5, Outside));
      Check (not HMI.Alarm_Active (5), "no alarm outside the zones");
      Alarms.Check (Track_At (5, Inside));
      Check (HMI.Alarm_Active (5), "alarm when entering a zone");
   end Test_Alarm_On_Entry;

   --  Verifies: SRS-0010
   procedure Test_Alarm_Kept_Until_Acknowledged is
   begin
      Alarms.Check (Track_At (5, Inside));
      Check (HMI.Alarm_Active (5), "alarm kept while inside");
      HMI.Acknowledge (5);
      Check (not HMI.Alarm_Active (5), "alarm cleared when acknowledged");
   end Test_Alarm_Kept_Until_Acknowledged;

begin
   Test_Alarm_On_Entry;
   Test_Alarm_Kept_Until_Acknowledged;
   if Failures = 0 then
      Put_Line ("ALL PASSED");
   else
      Put_Line (Natural'Image (Failures) & " FAILED");
   end if;
end Test_Alarms;
