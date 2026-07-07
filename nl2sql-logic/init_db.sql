--
-- PostgreSQL database dump
--

\restrict xarmb2VbySNQUhqUS3eaPwd3EtgG86on4vcFRcXpg2K8D5JLPKJCdtbYEWHX1jz

-- Dumped from database version 14.20 (Homebrew)
-- Dumped by pg_dump version 14.20 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: conversation_history; Type: TABLE; Schema: public; Owner: 
--

CREATE TABLE public.conversation_history (
    id integer NOT NULL,
    conversation_id integer NOT NULL,
    message text NOT NULL,
    sender character varying(50) NOT NULL,
    "timestamp" timestamp without time zone DEFAULT now() NOT NULL,
    CONSTRAINT conversation_history_sender_check CHECK (((sender)::text = ANY ((ARRAY['user'::character varying, 'assistant'::character varying])::text[])))
);


--
-- Name: conversation_history_id_seq; Type: SEQUENCE; Schema: public; Owner: 
--

CREATE SEQUENCE public.conversation_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: conversation_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: 
--

ALTER SEQUENCE public.conversation_history_id_seq OWNED BY public.conversation_history.id;


--
-- Name: conversations; Type: TABLE; Schema: public; Owner: 
--

CREATE TABLE public.conversations (
    id integer NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    db_url text,
    database_type character varying(50),
    name text,
    user_id integer
);



--
-- Name: conversations_id_seq; Type: SEQUENCE; Schema: public; Owner: 
--

CREATE SEQUENCE public.conversations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--

ALTER SEQUENCE public.conversations_id_seq OWNED BY public.conversations.id;


--
-- Name: query_feedback; Type: TABLE; Schema: public; Owner: 
--

CREATE TABLE public.query_feedback (
    id integer NOT NULL,
    conversation_id character varying(255),
    user_question text,
    generated_sql text,
    feedback_type character varying(20),
    corrected_sql text,
    user_notes text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);



--
-- Name: query_feedback_id_seq; Type: SEQUENCE; Schema: public; Owner: 
--

CREATE SEQUENCE public.query_feedback_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: query_feedback_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: 
--

ALTER SEQUENCE public.query_feedback_id_seq OWNED BY public.query_feedback.id;


--
-- Name: query_results; Type: TABLE; Schema: public; Owner:
--

CREATE TABLE public.query_results (
    id integer NOT NULL,
    conversation_id integer NOT NULL,
    sql_query text NOT NULL,
    result text,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);



--
-- Name: query_results_id_seq; Type: SEQUENCE; Schema: public; Owner: 
--

CREATE SEQUENCE public.query_results_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: query_results_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: 
--

ALTER SEQUENCE public.query_results_id_seq OWNED BY public.query_results.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: 
--

CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying(50) NOT NULL,
    email character varying(100),
    password character varying(200) NOT NULL
);


--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: 
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: 
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: conversation_history id; Type: DEFAULT; Schema: public; Owner: 
--

ALTER TABLE ONLY public.conversation_history ALTER COLUMN id SET DEFAULT nextval('public.conversation_history_id_seq'::regclass);


--
-- Name: conversations id; Type: DEFAULT; Schema: public; Owner: 
--

ALTER TABLE ONLY public.conversations ALTER COLUMN id SET DEFAULT nextval('public.conversations_id_seq'::regclass);


--
-- Name: query_feedback id; Type: DEFAULT; Schema: public; Owner: 
--

ALTER TABLE ONLY public.query_feedback ALTER COLUMN id SET DEFAULT nextval('public.query_feedback_id_seq'::regclass);


--
-- Name: query_results id; Type: DEFAULT; Schema: public; Owner: 
--

ALTER TABLE ONLY public.query_results ALTER COLUMN id SET DEFAULT nextval('public.query_results_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: 
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: conversation_history conversation_history_pkey; Type: CONSTRAINT; Schema: public; Owner: 
--

ALTER TABLE ONLY public.conversation_history
    ADD CONSTRAINT conversation_history_pkey PRIMARY KEY (id);


--
-- Name: conversations conversations_pkey; Type: CONSTRAINT; Schema: public; Owner: 
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_pkey PRIMARY KEY (id);


--
-- Name: query_feedback query_feedback_pkey; Type: CONSTRAINT; Schema: public; Owner: 
--

ALTER TABLE ONLY public.query_feedback
    ADD CONSTRAINT query_feedback_pkey PRIMARY KEY (id);


--
-- Name: query_results query_results_pkey; Type: CONSTRAINT; Schema: public; Owner: 
--

ALTER TABLE ONLY public.query_results
    ADD CONSTRAINT query_results_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: 
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: idx_conversation_history_conversation_id; Type: INDEX; Schema: public; Owner: 
--

CREATE INDEX idx_conversation_history_conversation_id ON public.conversation_history USING btree (conversation_id);


--
-- Name: idx_conversation_history_timestamp; Type: INDEX; Schema: public; Owner: 
--

CREATE INDEX idx_conversation_history_timestamp ON public.conversation_history USING btree ("timestamp");


--
-- Name: idx_query_results_conversation_id; Type: INDEX; Schema: public; Owner: 
--

CREATE INDEX idx_query_results_conversation_id ON public.query_results USING btree (conversation_id);


--
-- Name: idx_query_results_created_at; Type: INDEX; Schema: public; Owner: 
--

CREATE INDEX idx_query_results_created_at ON public.query_results USING btree (created_at);


--
-- Name: conversation_history conversation_history_conversation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: 
--

ALTER TABLE ONLY public.conversation_history
    ADD CONSTRAINT conversation_history_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES public.conversations(id) ON DELETE CASCADE;


--
-- Name: conversations conversations_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: 
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: query_results query_results_conversation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: 
--

ALTER TABLE ONLY public.query_results
    ADD CONSTRAINT query_results_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES public.conversations(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict xarmb2VbySNQUhqUS3eaPwd3EtgG86on4vcFRcXpg2K8D5JLPKJCdtbYEWHX1jz

