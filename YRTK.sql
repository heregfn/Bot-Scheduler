PGDMP     6                     {            YRTK    15.1    15.1                0    0    ENCODING    ENCODING        SET client_encoding = 'UTF8';
                      false                       0    0 
   STDSTRINGS 
   STDSTRINGS     (   SET standard_conforming_strings = 'on';
                      false                       0    0 
   SEARCHPATH 
   SEARCHPATH     8   SELECT pg_catalog.set_config('search_path', '', false);
                      false                       1262    398223    YRTK    DATABASE     z   CREATE DATABASE "YRTK" WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'Russian_Russia.1251';
    DROP DATABASE "YRTK";
                postgres    false            �            1255    447458    schedule_trigger_function()    FUNCTION     U  CREATE FUNCTION public.schedule_trigger_function() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  IF NEW = OLD THEN
    -- Новое значение совпадает со старым, ничего не делаем
    RETURN NULL;
  ELSE
    -- Вставляем измененные данные в таблицу истории
    INSERT INTO schedule_history (group_name, subject_name, subject_name_1, subject_name_2,
      teacher_name, teacher_name_1, teacher_name_2, classroom, classroom_1, classroom_2,
      start_time, end_time, id_shelude)
    VALUES (NEW.group_name, NEW.subject_name, NEW.subject_name_1, NEW.subject_name_2,
      NEW.teacher_name, NEW.teacher_name_1, NEW.teacher_name_2, NEW.classroom, NEW.classroom_1, NEW.classroom_2,
      NEW.start_time, NEW.end_time, NEW.id_shelude);
    RETURN NEW;
  END IF;
END;
$$;
 2   DROP FUNCTION public.schedule_trigger_function();
       public          postgres    false            �            1255    398238    set_group(text, text, text)    FUNCTION     �  CREATE FUNCTION public.set_group(user_id_main text, group_main text, username_main text) RETURNS character varying
    LANGUAGE plpgsql
    AS $$
DECLARE
    result VARCHAR;
BEGIN
    IF EXISTS (SELECT 1 FROM users WHERE user_id = user_id_main::text) THEN
        UPDATE users SET username=username_main::text, "group"=group_main::text WHERE user_id = user_id_main::text;
        result := 'Ok';
    ELSE
        -- Создание новой записи пользователя
        INSERT INTO users (user_id, username, "group") VALUES (user_id_main::text, username_main::text, group_main::text);
        result := 'No found';
    END IF;
    
    RETURN result;
END;
$$;
 X   DROP FUNCTION public.set_group(user_id_main text, group_main text, username_main text);
       public          postgres    false            �            1255    398236 '   update_user(integer, character varying)    FUNCTION     �  CREATE FUNCTION public.update_user(user_id_main integer, username_main character varying) RETURNS character varying
    LANGUAGE plpgsql
    AS $$
DECLARE
    result VARCHAR;
BEGIN
    -- Проверка наличия пользователя в таблице users
    IF EXISTS (SELECT 1 FROM users WHERE user_id = user_id_main::text) THEN
		IF EXISTS (SELECT register FROM users WHERE user_id = user_id_main::text and register is true) THEN
			-- Обновление записи пользователя
			UPDATE users SET username=username_main::text WHERE user_id = user_id_main::text;
			result := 'Ok';
		ELSE
			result := 'No found';
		END IF;
    ELSE
        -- Создание новой записи пользователя
        INSERT INTO users (user_id, username) VALUES (user_id_main::text, username_main::text);
        result := 'No found';
    END IF;
    
    RETURN result;
END;
$$;
 Y   DROP FUNCTION public.update_user(user_id_main integer, username_main character varying);
       public          postgres    false            �            1259    448218    edit_text_data    TABLE     m   CREATE TABLE public.edit_text_data (
    id integer NOT NULL,
    day text,
    pars text,
    split text
);
 "   DROP TABLE public.edit_text_data;
       public         heap    postgres    false            �            1259    448217    edit_text_data_id_seq    SEQUENCE     �   ALTER TABLE public.edit_text_data ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.edit_text_data_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);
            public          postgres    false    220            �            1259    447694    schedule    TABLE     N  CREATE TABLE public.schedule (
    group_name text,
    subject_name text,
    subject_name_1 text,
    subject_name_2 text,
    teacher_name text,
    teacher_name_1 text,
    teacher_name_2 text,
    classroom text,
    classroom_1 text,
    classroom_2 text,
    start_time text,
    end_time text,
    id_shelude text NOT NULL
);
    DROP TABLE public.schedule;
       public         heap    postgres    false            �            1259    447701    schedule_history    TABLE     �  CREATE TABLE public.schedule_history (
    group_name text,
    subject_name text,
    subject_name_1 text,
    subject_name_2 text,
    teacher_name text,
    teacher_name_1 text,
    teacher_name_2 text,
    classroom text,
    classroom_1 text,
    classroom_2 text,
    start_time text,
    end_time text,
    id_shelude text NOT NULL,
    id_shelude_history integer NOT NULL,
    accepted boolean DEFAULT false
);
 $   DROP TABLE public.schedule_history;
       public         heap    postgres    false            �            1259    447746 '   schedule_history_id_shelude_history_seq    SEQUENCE     �   ALTER TABLE public.schedule_history ALTER COLUMN id_shelude_history ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.schedule_history_id_shelude_history_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);
            public          postgres    false    216            �            1259    447727    schedule_temp    TABLE     S  CREATE TABLE public.schedule_temp (
    group_name text,
    subject_name text,
    subject_name_1 text,
    subject_name_2 text,
    teacher_name text,
    teacher_name_1 text,
    teacher_name_2 text,
    classroom text,
    classroom_1 text,
    classroom_2 text,
    start_time text,
    end_time text,
    id_shelude text NOT NULL
);
 !   DROP TABLE public.schedule_temp;
       public         heap    postgres    false            �            1259    398224    users    TABLE       CREATE TABLE public.users (
    user_id text NOT NULL,
    username text,
    "group" text,
    notifing text DEFAULT 0,
    auto_send text DEFAULT 0,
    group_pod text DEFAULT 0,
    used_text text DEFAULT 1,
    register boolean DEFAULT false,
    auto_send_time integer DEFAULT 5
);
    DROP TABLE public.users;
       public         heap    postgres    false            �           2606    448224 "   edit_text_data edit_text_data_pkey 
   CONSTRAINT     `   ALTER TABLE ONLY public.edit_text_data
    ADD CONSTRAINT edit_text_data_pkey PRIMARY KEY (id);
 L   ALTER TABLE ONLY public.edit_text_data DROP CONSTRAINT edit_text_data_pkey;
       public            postgres    false    220            �           2606    447754 &   schedule_history schedule_history_pkey 
   CONSTRAINT     t   ALTER TABLE ONLY public.schedule_history
    ADD CONSTRAINT schedule_history_pkey PRIMARY KEY (id_shelude_history);
 P   ALTER TABLE ONLY public.schedule_history DROP CONSTRAINT schedule_history_pkey;
       public            postgres    false    216            �           2606    447700    schedule schedule_pkey 
   CONSTRAINT     \   ALTER TABLE ONLY public.schedule
    ADD CONSTRAINT schedule_pkey PRIMARY KEY (id_shelude);
 @   ALTER TABLE ONLY public.schedule DROP CONSTRAINT schedule_pkey;
       public            postgres    false    215            �           2606    447733     schedule_temp schedule_temp_pkey 
   CONSTRAINT     f   ALTER TABLE ONLY public.schedule_temp
    ADD CONSTRAINT schedule_temp_pkey PRIMARY KEY (id_shelude);
 J   ALTER TABLE ONLY public.schedule_temp DROP CONSTRAINT schedule_temp_pkey;
       public            postgres    false    217            �           2606    398232    users users_pkey 
   CONSTRAINT     S   ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (user_id);
 :   ALTER TABLE ONLY public.users DROP CONSTRAINT users_pkey;
       public            postgres    false    214            �           2620    447706    schedule schedule_trigger    TRIGGER     �   CREATE TRIGGER schedule_trigger AFTER UPDATE ON public.schedule FOR EACH ROW EXECUTE FUNCTION public.schedule_trigger_function();
 2   DROP TRIGGER schedule_trigger ON public.schedule;
       public          postgres    false    215    233           