with Ada.Text_IO;
with HMI;
with Logger;

package body Track_Store is

   Table : array (Track_Id) of Track;

   --  Req: SRS-0003, SRS-0011
   procedure Create
     (Target : Positive;
      Pos    : Position;
      Now    : Seconds;
      Id     : out Track_Id;
      Ok     : out Boolean) is
   begin
      for I in Table'Range loop
         if not Table (I).In_Use then
            Table (I) := (Id          => I,
                          Target      => Target,
                          Pos         => Pos,
                          Last_Report => Now,
                          In_Use      => True);
            Id := I;
            Ok := True;
            HMI.Show_Track (Table (I));
            return;
         end if;
      end loop;
      Id := Track_Id'First;
      Ok := False;
      Logger.Log ("Track table full, report ignored");
   end Create;

   --  Req: SRS-0005
   procedure Update (Id : Track_Id; Pos : Position; Now : Seconds) is
   begin
      Table (Id).Pos := Pos;
      Table (Id).Last_Report := Now;
      HMI.Show_Track (Table (Id));
   end Update;

   --  Req: SRS-0006, SRS-0008
   procedure Delete (Id : Track_Id) is
   begin
      if Table (Id).In_Use then
         Table (Id).In_Use := False;
         HMI.Remove_Track (Id);
         Logger.Log ("Track" & Track_Id'Image (Id) & " deleted");
      end if;
   end Delete;

   --  Req: SRS-0004
   procedure Purge_Stale (Now : Seconds) is
   begin
      for I in Table'Range loop
         if Table (I).In_Use
           and then Now - Table (I).Last_Report >= Stale_Timeout
         then
            Delete (I);
         end if;
      end loop;
   end Purge_Stale;

   procedure Find
     (Target : Positive; Id : out Track_Id; Found : out Boolean) is
   begin
      for T of Table loop
         if T.In_Use and then T.Target = Target then
            Id := T.Id;
            Found := True;
            return;
         end if;
      end loop;
      Id := Track_Id'First;
      Found := False;
   end Find;

   function Exists (Id : Track_Id) return Boolean is (Table (Id).In_Use);

   function Get (Id : Track_Id) return Track is (Table (Id));

   function Count return Natural is
      N : Natural := 0;
   begin
      for T of Table loop
         if T.In_Use then
            N := N + 1;
         end if;
      end loop;
      return N;
   end Count;

   procedure Dump is
   begin
      for T of Table loop
         if T.In_Use then
            Ada.Text_IO.Put_Line
              ("Track" & Track_Id'Image (T.Id)
               & " target" & Natural'Image (T.Target)
               & " at" & Float'Image (T.Pos.X) & Float'Image (T.Pos.Y));
         end if;
      end loop;
   end Dump;

end Track_Store;
