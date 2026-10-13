with Ada.Text_IO; use Ada.Text_IO;
with Tracks;      use Tracks;
with Track_Store;

--  Unit tests of Track_Store.
procedure Test_Track_Store is

   Failures : Natural := 0;

   procedure Check (Condition : Boolean; Name : String) is
   begin
      if Condition then
         Put_Line ("PASS " & Name);
      else
         Put_Line ("FAIL " & Name);
         Failures := Failures + 1;
      end if;
   end Check;

   --  Req: SRS-0004
   procedure Test_Stale_Track_Is_Purged is
      Id : Track_Id;
      Ok : Boolean;
   begin
      Track_Store.Create (Target => 1, Pos => (100.0, 200.0), Now => 0.0,
                          Id => Id, Ok => Ok);
      Track_Store.Purge_Stale (Now => 9.0);
      Check (Track_Store.Exists (Id), "track kept before the timeout");
      Track_Store.Purge_Stale (Now => 10.0);
      Check (not Track_Store.Exists (Id), "track deleted at the timeout");
   end Test_Stale_Track_Is_Purged;

   --  Req: SRS-0006
   procedure Test_Operator_Delete is
      Id : Track_Id;
      Ok : Boolean;
   begin
      Track_Store.Create (Target => 2, Pos => (0.0, 0.0), Now => 0.0,
                          Id => Id, Ok => Ok);
      Track_Store.Delete (Id);
      Check (not Track_Store.Exists (Id), "track deleted on operator request");
   end Test_Operator_Delete;

begin
   Test_Stale_Track_Is_Purged;
   Test_Operator_Delete;
   if Failures = 0 then
      Put_Line ("ALL PASSED");
   else
      Put_Line (Natural'Image (Failures) & " FAILED");
   end if;
end Test_Track_Store;
