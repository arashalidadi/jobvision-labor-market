---
license: cc-by-nc-4.0
language:
- fa
- en
pretty_name: JobVision Jobposts Dataset
size_categories:
- 100K<n<1M
task_categories:
- tabular-regression
- tabular-classification
- text-classification
tags:
- recruitment
- labor-market
- jobs
- iran
- salary-prediction
---

# 💼 JobVision JobPosts Dataset 
 - ### 📁 Dataset Name: JobVision_Jobposts_Dataset
 - ### 🗂️ Source: JobVision
 - ### 📊 Size: ~365k rows 
 - ### 🗓️ Release Date: August 2025
 - ### 🌍 Languages: Persian (primary), English translations for key fields 
 - ### 📄 Format: CSV (tabular)
 - ### 📚 Domain: Recruitment, Human Resources, Labor‑Market Analytics
 - ### 🗓️ Time Period: 2022–2024

# 📋 Overview
The `JobVision_Jobposts_Dataset` contains anonymized job advertisements from Jobvision, Iran’s largest online jobboard. This dataset provides granular insights into Iran’s labor market, including job requirements, salary ranges, and skill demands. Ideal for HR analytics and labor economics research.

# 📊 Schema
## 🏷️ Job Metadata
  - ` Jobpost_RawTitle `: Job title (e.g., "برنامه نویس full-stack")
  - `Jobpost_PreferredGender`: e.g., "ترجیحاً آقا"
  - `Jobpost_ProvinceFa/Jobpost_ProvinceEn`: Location (e.g., "Tehran")
  - `Jobpost_WorkTypeEn/Jobpost_WorkTypeFa`: Employment type (Full Time, Part Time)
  - `Jobpost_SalaryCanBeShown`: Whether salary is disclosed (True/False)
  - `Jobpost_MinSalary/Jobpost_MaxSalary`: Salary range (in Iranian Toman)
  - `Jobpost_RequiredExperienceYears`: Years of experience required
  - `Other Feature`:  Jobpost_RequiredRelatedExperienceInThisIndustry, Jobpost_CompanyWorkTimesDescription, Jobpost_ActivationTime_YEAR_MONTH

## 📝 Categorization
  - `Jobpost_MainJobCategory` :  e.g., "مالی و حسابداری"
  - `Jobpost_SecondaryJobCategories`

## 🛠️ Skills & Qualifications
  - `Jobpost_SoftwareSkills`: JSON list of tools (e.g., [{"TitleFa":"پایتون","TitleEn":"Python","Level":"پیشرفته"},{"TitleFa":"","TitleEn":"PostgreSql","Level":"پیشرفته"}])
  - `Jobpost_LanguageSkills`: Language proficiency (e.g., [{"Languages_TitleFa":"انگلیسی","Languages_TitleEn":"English","Level":"متوسط ۵۰٪"}])

## 🏢 Company Details
  - `Company_ProvinceEn/Company_CityEn`: Location (e.g., "Tehran")
  - `Company_SizeEn/Company_SizeFa`: Employee count (e.g., "11-50 employees")
  - `Company_IndustryEn`: Industry sector (e.g., "IT / Software / Hardware")
  - `Other Feature`: Company_AgeFromEstablishmentYear, Company_CompanyOwnershipTypesEn, Company_ActivityType
## 🌐 Benefits & Policies
  - `Jobpost_BenefitEn/Jobpost_BenefitFa`: Benefits (e.g., "Health insurance, Commision")
  - `Jobpost_IsRemote`: Remote work availability (True/False)
  - `Jobpost_HasDisabilitySupport`: Disability accommodations (True/False)
  - `Jobpost_RequiredMinAge/Jobpost_RequiredMaxAge`
  - `Jobpost_RequiredMilitaryServiceCard`: (True/False)


# 💡 Use Cases
1. **Salary Prediction**: Estimate expected compensation given jobpost feature.
   * Labor Market Analysis
   * Identify regional skill gaps (e.g., React developers in Isfahan).
4. **Track salary trends by industry/experience.**
5. **Geospatial Visualization**: Map job density and salary variance by region.
6. **Company Hiring Strategy**
   * Benchmark benefits (e.g., 43% of tech jobs offer remote work).
   * Analyze gender-specific roles (Jobpost_PreferredGender).
5. **Demand Forecasting**: Track hiring trends across industries and provinces.

## 📜 License

This dataset is released under the **Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)** license.

- ✅ **Research, academic, and other non-commercial use** is permitted, provided that appropriate credit is given to JobVision.
- ❌ **Commercial use** (including use in commercial products or services, or training models for commercial purposes) is **not permitted** under this license.

For commercial licensing, please contact **[info@jobvision.ir](mailto:info@jobvision.ir)**.

Full license text: https://creativecommons.org/licenses/by-nc/4.0/

# 🤝 Contributing
We welcome contributions to improve this dataset! If you find issues or have suggestions, please contact us at info@jobvision.ir.
