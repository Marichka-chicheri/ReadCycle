variable "region" {
  type    = string
  default = "eu-central-1"
}

variable "github_repo" {
  description = "GitHub repository allowed to deploy, as owner/name"
  type        = string
  default     = "Marichka-chicheri/ReadCycle"
}

variable "github_branch" {
  description = "Branch whose pushes may deploy"
  type        = string
  default     = "main"
}
