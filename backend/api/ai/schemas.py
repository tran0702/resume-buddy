"""
Shared data schemas for Resume Buddy.
These Python dataclasses mirror the TypeScript interfaces in:
  src/renderer/src/types/schema.ts

Any change here must be reflected there and vice versa.
Serialization: use dataclasses.asdict() before passing to jsonify().
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


# ====== Master Profile ======

@dataclass
class ContactInfo:
    name: str
    email: str
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None


@dataclass
class WorkExperience:
    company: str
    title: str
    start_date: str
    end_date: Optional[str] = None   # None = present
    location: Optional[str] = None
    bullets: list[str] = field(default_factory=list)


@dataclass
class Education:
    institution: str
    degree: str
    field_of_study: str
    graduation_date: str
    gpa: Optional[float] = None
    honors: list[str] = field(default_factory=list)


@dataclass
class Project:
    name: str
    description: str
    bullets: list[str] = field(default_factory=list)
    technologies: list[str] = field(default_factory=list)
    url: Optional[str] = None


@dataclass
class MasterProfile:
    contact: ContactInfo
    work_experience: list[WorkExperience] = field(default_factory=list)
    education: list[Education] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    summary: Optional[str] = None
    certifications: list[str] = field(default_factory=list)
    projects: list[Project] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)
    volunteer: list[str] = field(default_factory=list)


# ====== Job Analysis ======

@dataclass
class JobRequirement:
    skill: str
    importance: str   # 'required' | 'preferred' | 'nice-to-have'


@dataclass
class JobAnalysis:
    job_title: str
    required_skills: list[str] = field(default_factory=list)
    preferred_skills: list[str] = field(default_factory=list)
    key_responsibilities: list[str] = field(default_factory=list)
    keywords_for_ats: list[str] = field(default_factory=list)
    raw_requirements: list[JobRequirement] = field(default_factory=list)
    company_name: Optional[str] = None
    years_experience_required: Optional[int] = None
    education_required: Optional[str] = None
    industry: Optional[str] = None
    seniority_level: Optional[str] = None
    company_values: list[str] = field(default_factory=list)


# ====== Generated Document ======

@dataclass
class GeneratedDocument:
    document_type: str     # 'resume' | 'cover_letter' | 'interview_prep'
    job_title: str
    content: str
    generated_at: str      # ISO 8601 timestamp
    company_name: Optional[str] = None
    tailoring_notes: list[str] = field(default_factory=list)
    ats_match_score: Optional[int] = None
