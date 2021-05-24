start transaction;
set @id:=2;
delete from journal_log where user_id=@id;
delete from activity_counter where user_id=@id;
delete from activity_counter where user_id=@id;
delete from crime where user_id=@id;
delete from earning_historys where user_id=@id;
delete from edmc where user_id=@id;
delete from faction_activity where user_id=@id;
delete from parser_log where user_id=@id;
commit;

