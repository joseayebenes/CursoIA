with Tracks; use Tracks;

--  The table of current tracks.
package Track_Store is

   procedure Create
     (Target : Positive;
      Pos    : Position;
      Now    : Seconds;
      Id     : out Track_Id;
      Ok     : out Boolean);
   --  Creates a track for a new target. Ok is False if the table is full.

   procedure Update (Id : Track_Id; Pos : Position; Now : Seconds);
   --  A new report for an existing track.

   procedure Delete (Id : Track_Id);
   --  Deletes a track. The operator asks for it from the HMI; Purge_Stale
   --  uses it too.

   procedure Purge_Stale (Now : Seconds);
   --  Deletes every track with no report for Stale_Timeout.
   --  To be called once per Purge_Period.

   procedure Find
     (Target : Positive; Id : out Track_Id; Found : out Boolean);
   --  The track of a sensor target, if it has one.

   function Exists (Id : Track_Id) return Boolean;

   function Get (Id : Track_Id) return Track;

   function Count return Natural;

   procedure Dump;
   --  Lists the tracks on standard output, for debugging.

end Track_Store;
