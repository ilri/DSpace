/*
 * The contents of this file are subject to the license and copyright
 * detailed in the LICENSE and NOTICE files at the root of the source
 * tree and available online at
 *
 * http://www.dspace.org/license/
 */
// Generated on 2013-11-09 using generator-webapp 0.4.3
'use strict';

module.exports = function (grunt) {
    const sass = require('node-sass');

    grunt.loadNpmTasks('grunt-postcss');
    grunt.loadNpmTasks('grunt-contrib-watch');
    grunt.loadNpmTasks('grunt-string-replace');
    grunt.loadNpmTasks('grunt-webpack');

    // show elapsed time at the end
    require('time-grunt')(grunt);
    // load all grunt tasks
    require('load-grunt-tasks')(grunt);

    // help webpack derive an absolute path
    var path = require('path');

    grunt.initConfig({
        copy: {
            classic_mirage_color_scheme: {
                files: [
                    {
                        src: ['styles/classic_mirage_color_scheme/_main.scss'],
                        dest: 'styles/main.scss'
                    }
                ]
            },
            bootstrap_color_scheme: {
                files: [
                    {
                        src: ['styles/bootstrap_color_scheme/_main.scss'],
                        dest: 'styles/main.scss'
                    }
                ]
            },
            scriptsxml: {
                files: [
                    {
                        src: ['scripts.xml'],
                        dest: 'scripts-dist.xml'
                    }
                ]
            },
            ie8_scripts: {
                files: [
                    {
                        src: ['node_modules/html5shiv/dist/html5shiv.js'],
                        dest: 'scripts/html5shiv.js'
                    },
                    {
                        src: ['node_modules/respond.min.js/respond.min.js'],
                        dest: 'scripts/respond.min.js'
                    }
                ]
            },
            fonts: {
                files: [
                    {
                        src: 'node_modules/bootstrap-sass/assets/fonts/bootstrap/*',
                        expand: true,
                        flatten: true,
                        dest: 'fonts/bootstrap'
                    }
                ]
            }
        },
        'string-replace': {
            // Dirty hack to modify Atmire's statlets so they don't require
            // compass. Instead, we use the compass-mixins from npm so we
            // can compile our stylesheets with node-sass, which is much
            // more modern than Ruby sass.
            dist: {
                files: {
                    'styles/_statlets.scss': 'styles/_statlets.scss',
                },
                options: {
                    replacements: [
                        {
                            pattern: '@import "compass"',
                            replacement: '@import "../node_modules/compass-mixins/lib/compass"'
                        }
                    ]
                }
            }
        },
        sass: {
            options: {
                    implementation: sass
                },
            dist: {
                files: {
                    'styles/main.css': 'styles/main.scss'
                }
            }
        },
        // Compile Font Awesome JS to something that UglifyJS can use (the
        // Font Awesome 5 SVG JavaScript API is written in ES6, which uses
        // modules and requires, and UglifyJS doesn't support that syntax).
        // Here we use UMD format with requires inlined.
        webpack: {
            config: () => ({
                entry: './scripts/fontawesome.js',
                output: {
                    path: path.resolve(__dirname, 'scripts'),
                    filename: 'fontawesome.umd.js'
                },
                mode: 'production',
            }),
        },
        postcss: {
            prod: {
                options: {
                    processors: [
                        require('pixrem')(), // add fallbacks for rem units
                        require('autoprefixer')({browsers: 'last 2 versions'}), // add vendor prefixes
                        require('cssnano')() // minify the result
                    ]
                },
                src: 'styles/*.css'
            },
            dev: {
                options: {
                    map: true, // inline sourcemaps
                    processors: [
                        require('pixrem')(), // add fallbacks for rem units
                        require('autoprefixer')({browsers: 'last 2 versions'}), // add vendor prefixes
                    ]
                },
                src: 'styles/*.css'
            }
        },
        coffee: {
            glob_to_multiple: {
                expand: true,
                flatten: true,
                cwd: 'scripts',
                src: ['*.coffee'],
                dest: 'scripts',
                ext: '.js'
            }
        },
        handlebars: {
            compile: {
                options: {
                    namespace: "DSpace.templates",
                    processName: function(filePath) {
                        return filePath.replace(/^templates\//, '').replace(/\.handlebars$/, '').replace(/\.hbs$/, '');
                    }
                },
                files: {
                    "scripts/templates.js": ["templates/*.handlebars", "templates/*.hbs"]
                }
            }
        },
        useminPrepare:{
            src: ['scripts-dist.xml'],
            options: {
                // fool usemin in to putting theme.js straight into the scripts
                // folder, and not in a separate dist folder. And no, you can't
                // just use an empty string, I tried ;)
                dest: 'dist/../'
            }
        } ,
        usemin: {
            html:'scripts-dist.xml'
        },
        watch: {
            css: {
                files: ['**/*.scss', '!**/node_modules/**'],
                tasks: ['sass', 'postcss:dev'],
                options: {
                    livereload: true
                }
            },
            scripts: {
                files: ['scripts.xml', '**/*.js', '**/*.hbs', '**/*.coffee', '!**/node_modules/**', '!scripts/templates.js', '!scripts/theme.js'],
                tasks: ['no-compass-dev'],
                options: {
                    livereload: true
                }
            }
        }
    });


    grunt.registerTask('classic_mirage_color_scheme', [
        'copy:classic_mirage_color_scheme'
    ]);
    grunt.registerTask('bootstrap_color_scheme', [
        'copy:bootstrap_color_scheme'
    ]);
    grunt.registerTask('shared-steps', [
        'copy:scriptsxml', 'coffee', 'handlebars', 'useminPrepare','concat', 'copy:ie8_scripts', 'copy:fonts'
    ]);
    grunt.registerTask('no-compass-prod', [
        'shared-steps','uglify','usemin'
    ]);
    grunt.registerTask('no-compass-dev', [
        'shared-steps','uglify:generated'
    ]);
    grunt.registerTask('prod', [
        'string-replace', 'sass', 'webpack', 'postcss:prod', 'no-compass-prod'
    ]);
    grunt.registerTask('dev', [
        'classic_mirage_color_scheme', 'string-replace', 'webpack', 'sass', 'postcss:dev', 'no-compass-dev'
    ]);
    grunt.registerTask('default', [
        'classic_mirage_color_scheme',
        'prod'
    ]);
};
